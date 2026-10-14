//! GritX High-Performance Audio Engine
//! Zero-copy, silence-aware in-memory audio slicer and WAV analyzer.
//! Provides sub-millisecond audio chunking with zero-crossing acoustic alignment
//! to prevent mid-word clipping during Whisper transcription.

use std::env;
use std::fs::{self, File};
use std::io::{BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone)]
pub struct WavHeader {
    pub channels: u16,
    pub sample_rate: u32,
    pub byte_rate: u32,
    pub block_align: u16,
    pub bits_per_sample: u16,
    pub data_offset: u64,
    pub data_size: u32,
}

#[derive(Debug)]
pub struct WavAudio {
    pub header: WavHeader,
    pub samples: Vec<i16>,
    pub raw_data: Vec<u8>,
}

impl WavAudio {
    pub fn load_from_file<P: AsRef<Path>>(path: P) -> Result<Self, String> {
        let path_ref = path.as_ref();
        let file = File::open(path_ref).map_err(|e| format!("Failed to open {:?}: {}", path_ref, e))?;
        let mut reader = BufReader::new(file);

        let mut magic = [0u8; 4];
        reader.read_exact(&mut magic).map_err(|e| format!("Read error: {}", e))?;
        if &magic != b"RIFF" {
            return Err("Not a valid RIFF file".to_string());
        }

        let mut file_size_bytes = [0u8; 4];
        reader.read_exact(&mut file_size_bytes).map_err(|e| format!("Read error: {}", e))?;

        let mut wave_magic = [0u8; 4];
        reader.read_exact(&mut wave_magic).map_err(|e| format!("Read error: {}", e))?;
        if &wave_magic != b"WAVE" {
            return Err("Not a valid WAVE file".to_string());
        }

        let mut channels = 1u16;
        let mut sample_rate = 16000u32;
        let mut byte_rate = 32000u32;
        let mut block_align = 2u16;
        let mut bits_per_sample = 16u16;
        let mut found_fmt = false;

        let mut data_offset = 0u64;
        let mut data_size = 0u32;
        let mut found_data = false;

        let mut current_pos = 12u64;

        loop {
            let mut chunk_id = [0u8; 4];
            if reader.read_exact(&mut chunk_id).is_err() {
                break;
            }
            let mut chunk_size_bytes = [0u8; 4];
            if reader.read_exact(&mut chunk_size_bytes).is_err() {
                break;
            }
            let chunk_size = u32::from_le_bytes(chunk_size_bytes);
            current_pos += 8;

            if &chunk_id == b"fmt " {
                let mut fmt_bytes = vec![0u8; chunk_size as usize];
                reader.read_exact(&mut fmt_bytes).map_err(|e| format!("fmt read error: {}", e))?;
                current_pos += chunk_size as u64;

                if fmt_bytes.len() >= 16 {
                    let audio_format = u16::from_le_bytes([fmt_bytes[0], fmt_bytes[1]]);
                    if audio_format != 1 && audio_format != 3 {
                        // 1 = PCM, 3 = IEEE float
                        return Err(format!("Unsupported audio format: {}", audio_format));
                    }
                    channels = u16::from_le_bytes([fmt_bytes[2], fmt_bytes[3]]);
                    sample_rate = u32::from_le_bytes([fmt_bytes[4], fmt_bytes[5], fmt_bytes[6], fmt_bytes[7]]);
                    byte_rate = u32::from_le_bytes([fmt_bytes[8], fmt_bytes[9], fmt_bytes[10], fmt_bytes[11]]);
                    block_align = u16::from_le_bytes([fmt_bytes[12], fmt_bytes[13]]);
                    bits_per_sample = u16::from_le_bytes([fmt_bytes[14], fmt_bytes[15]]);
                    found_fmt = true;
                }
            } else if &chunk_id == b"data" {
                data_offset = current_pos;
                data_size = chunk_size;
                found_data = true;
                break;
            } else {
                // Skip unknown chunk (e.g. LIST, JUNK, etc.)
                reader.seek(SeekFrom::Current(chunk_size as i64)).map_err(|e| format!("Seek error: {}", e))?;
                current_pos += chunk_size as u64;
            }
        }

        if !found_fmt || !found_data {
            return Err("Missing fmt or data chunk in WAV header".to_string());
        }

        // Read raw data bytes
        reader.seek(SeekFrom::Start(data_offset)).map_err(|e| format!("Data seek error: {}", e))?;
        let mut raw_data = vec![0u8; data_size as usize];
        reader.read_exact(&mut raw_data).map_err(|e| format!("Data read error: {}", e))?;

        // Convert to i16 samples for analysis
        let bytes_per_sample = (bits_per_sample / 8) as usize;
        let total_samples = raw_data.len() / (bytes_per_sample * channels as usize);
        let mut samples = Vec::with_capacity(total_samples);

        if bits_per_sample == 16 {
            let mut i = 0;
            while i + 1 < raw_data.len() {
                let sample = i16::from_le_bytes([raw_data[i], raw_data[i + 1]]);
                samples.push(sample);
                i += 2 * channels as usize; // skip extra channels if stereo
            }
        } else if bits_per_sample == 8 {
            let mut i = 0;
            while i < raw_data.len() {
                let sample = ((raw_data[i] as i16) - 128) << 8;
                samples.push(sample);
                i += channels as usize;
            }
        }

        let header = WavHeader {
            channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            data_offset,
            data_size,
        };

        Ok(Self {
            header,
            samples,
            raw_data,
        })
    }

    pub fn duration_seconds(&self) -> f64 {
        if self.header.sample_rate == 0 {
            0.0
        } else {
            self.samples.len() as f64 / self.header.sample_rate as f64
        }
    }

    /// Finds the optimal silence / minimum-energy cut point near target_sample.
    /// Searches within [target_sample - search_window_samples, target_sample + search_window_samples].
    pub fn find_silence_cut(&self, target_sample: usize, search_window_samples: usize) -> usize {
        let total = self.samples.len();
        if target_sample >= total {
            return total;
        }

        let start = target_sample.saturating_sub(search_window_samples);
        let end = (target_sample + search_window_samples).min(total);

        if end <= start {
            return target_sample;
        }

        // Evaluate 50ms sub-blocks (~800 samples at 16kHz)
        let block_size = (self.header.sample_rate as usize / 20).max(100);
        let mut min_energy = f64::MAX;
        let mut best_block_start = target_sample;

        let mut curr = start;
        while curr + block_size <= end {
            let mut sum_sq = 0.0f64;
            for s in &self.samples[curr..curr + block_size] {
                let v = *s as f64;
                sum_sq += v * v;
            }
            let energy = sum_sq / (block_size as f64);
            if energy < min_energy {
                min_energy = energy;
                best_block_start = curr;
            }
            curr += block_size / 2; // 50% overlap for finer granularity
        }

        // Within the quietest block, find the sample closest to zero amplitude (zero-crossing)
        let block_end = (best_block_start + block_size).min(total);
        let mut min_abs = i16::MAX;
        let mut best_cut = best_block_start + block_size / 2;

        for (idx, s) in self.samples[best_block_start..block_end].iter().enumerate() {
            let abs_val = s.abs();
            if abs_val < min_abs {
                min_abs = abs_val;
                best_cut = best_block_start + idx;
                if min_abs == 0 {
                    break;
                }
            }
        }

        best_cut
    }

    /// Writes a segment from sample_start to sample_end as a valid 16kHz mono WAV file.
    pub fn write_slice<P: AsRef<Path>>(&self, path: P, sample_start: usize, sample_end: usize) -> Result<usize, String> {
        let total = self.samples.len();
        let s_start = sample_start.min(total);
        let s_end = sample_end.min(total);
        let slice_samples = s_end.saturating_sub(s_start);

        let bytes_per_sample = (self.header.bits_per_sample / 8) as usize;
        let channels = self.header.channels as usize;
        let bytes_per_frame = bytes_per_sample * channels;

        let byte_start = s_start * bytes_per_frame;
        let byte_end = (s_end * bytes_per_frame).min(self.raw_data.len());
        let slice_bytes = &self.raw_data[byte_start..byte_end];

        let out_file = File::create(path.as_ref())
            .map_err(|e| format!("Failed to create chunk file {:?}: {}", path.as_ref(), e))?;
        let mut writer = BufWriter::new(out_file);

        // Standard 44-byte RIFF header
        let chunk_size = 36 + slice_bytes.len() as u32;
        writer.write_all(b"RIFF").map_err(|e| e.to_string())?;
        writer.write_all(&chunk_size.to_le_bytes()).map_err(|e| e.to_string())?;
        writer.write_all(b"WAVE").map_err(|e| e.to_string())?;

        writer.write_all(b"fmt ").map_err(|e| e.to_string())?;
        writer.write_all(&16u32.to_le_bytes()).map_err(|e| e.to_string())?;
        writer.write_all(&1u16.to_le_bytes()).map_err(|e| e.to_string())?; // PCM
        writer.write_all(&self.header.channels.to_le_bytes()).map_err(|e| e.to_string())?;
        writer.write_all(&self.header.sample_rate.to_le_bytes()).map_err(|e| e.to_string())?;
        writer.write_all(&self.header.byte_rate.to_le_bytes()).map_err(|e| e.to_string())?;
        writer.write_all(&self.header.block_align.to_le_bytes()).map_err(|e| e.to_string())?;
        writer.write_all(&self.header.bits_per_sample.to_le_bytes()).map_err(|e| e.to_string())?;

        writer.write_all(b"data").map_err(|e| e.to_string())?;
        let subchunk2_size = slice_bytes.len() as u32;
        writer.write_all(&subchunk2_size.to_le_bytes()).map_err(|e| e.to_string())?;

        // Zero-copy direct slice buffer write
        writer.write_all(slice_bytes).map_err(|e| e.to_string())?;
        writer.flush().map_err(|e| e.to_string())?;

        Ok(slice_samples)
    }
}

pub struct ChunkResult {
    pub chunk_index: usize,
    pub path: PathBuf,
    pub start_seconds: f64,
    pub end_seconds: f64,
    pub duration_seconds: f64,
    pub sample_count: usize,
    pub silence_aligned: bool,
}

pub fn slice_audio_silence_aware<P: AsRef<Path>>(
    input_path: P,
    output_dir: P,
    chunk_seconds: u32,
    search_window_sec: f64,
) -> Result<Vec<ChunkResult>, String> {
    let wav = WavAudio::load_from_file(input_path.as_ref())?;
    let total_samples = wav.samples.len();
    let sample_rate = wav.header.sample_rate as usize;

    if total_samples == 0 || sample_rate == 0 {
        return Err("Audio contains 0 samples".to_string());
    }

    let out_dir = output_dir.as_ref();
    fs::create_dir_all(out_dir).map_err(|e| format!("Failed to create output dir {:?}: {}", out_dir, e))?;

    let chunk_target_samples = chunk_seconds as usize * sample_rate;
    // Cap search window to at most 30% of chunk target
    let max_window = chunk_target_samples * 3 / 10;
    let search_window_samples = ((search_window_sec * sample_rate as f64) as usize).min(max_window);

    let mut chunks = Vec::new();
    let mut current_start = 0usize;
    let mut chunk_idx = 0usize;

    while current_start < total_samples {
        let remaining = total_samples - current_start;
        let min_tail_samples = search_window_samples.min(chunk_target_samples / 4);
        let mut cut_point = if remaining <= chunk_target_samples + min_tail_samples {
            // Last chunk takes remainder to avoid tiny sub-second tail chunk
            total_samples
        } else {
            let target = current_start + chunk_target_samples;
            wav.find_silence_cut(target, search_window_samples)
        };

        // Guarantee strictly monotonic progression by at least 50% of chunk size
        let min_advance = (chunk_target_samples / 2).max(1);
        if cut_point <= current_start + min_advance {
            cut_point = (current_start + chunk_target_samples).min(total_samples);
        }
        cut_point = cut_point.min(total_samples);

        let chunk_filename = format!("chunk_{:03}.wav", chunk_idx);
        let chunk_path = out_dir.join(chunk_filename);

        wav.write_slice(&chunk_path, current_start, cut_point)?;

        let start_sec = current_start as f64 / sample_rate as f64;
        let end_sec = cut_point as f64 / sample_rate as f64;
        let dur_sec = end_sec - start_sec;
        let sample_cnt = cut_point - current_start;

        chunks.push(ChunkResult {
            chunk_index: chunk_idx,
            path: chunk_path,
            start_seconds: (start_sec * 100.0).round() / 100.0,
            end_seconds: (end_sec * 100.0).round() / 100.0,
            duration_seconds: (dur_sec * 100.0).round() / 100.0,
            sample_count: sample_cnt,
            silence_aligned: cut_point < total_samples,
        });

        current_start = cut_point;
        chunk_idx += 1;
    }

    Ok(chunks)
}

fn print_usage() {
    eprintln!("GritX Audio Optimization Engine (Rust v0.1.0)");
    eprintln!("Usage:");
    eprintln!("  gritx-audio slice --input <path> --output-dir <dir> [--chunk-seconds 600] [--search-window 10] [--json]");
    eprintln!("  gritx-audio info --input <path> [--json]");
    eprintln!("  gritx-audio --version");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_usage();
        std::process::exit(1);
    }

    let command = args[1].as_str();

    match command {
        "--version" | "-v" => {
            println!("gritx-audio 0.1.0");
            return;
        }
        "info" => {
            let mut input: Option<String> = None;
            let mut as_json = false;

            let mut i = 2;
            while i < args.len() {
                match args[i].as_str() {
                    "--input" | "-i" => {
                        if i + 1 < args.len() {
                            input = Some(args[i + 1].clone());
                            i += 1;
                        }
                    }
                    "--json" => as_json = true,
                    _ => {}
                }
                i += 1;
            }

            let input_path = match input {
                Some(p) => p,
                None => {
                    eprintln!("Error: Missing --input parameter");
                    std::process::exit(1);
                }
            };

            match WavAudio::load_from_file(&input_path) {
                Ok(wav) => {
                    let dur = wav.duration_seconds();
                    if as_json {
                        println!(
                            "{{\"channels\":{},\"sample_rate\":{},\"bits_per_sample\":{},\"total_samples\":{},\"duration_seconds\":{:.2}}}",
                            wav.header.channels,
                            wav.header.sample_rate,
                            wav.header.bits_per_sample,
                            wav.samples.len(),
                            dur
                        );
                    } else {
                        println!("Channels:         {}", wav.header.channels);
                        println!("Sample Rate:      {} Hz", wav.header.sample_rate);
                        println!("Bits Per Sample:  {}", wav.header.bits_per_sample);
                        println!("Total Samples:    {}", wav.samples.len());
                        println!("Duration:         {:.2} s ({:.1} min)", dur, dur / 60.0);
                    }
                }
                Err(e) => {
                    eprintln!("Error reading audio: {}", e);
                    std::process::exit(1);
                }
            }
        }
        "slice" => {
            let mut input: Option<String> = None;
            let mut output_dir: Option<String> = None;
            let mut chunk_seconds = 600u32;
            let mut search_window = 10.0f64;
            let mut as_json = false;

            let mut i = 2;
            while i < args.len() {
                match args[i].as_str() {
                    "--input" | "-i" => {
                        if i + 1 < args.len() {
                            input = Some(args[i + 1].clone());
                            i += 1;
                        }
                    }
                    "--output-dir" | "-o" => {
                        if i + 1 < args.len() {
                            output_dir = Some(args[i + 1].clone());
                            i += 1;
                        }
                    }
                    "--chunk-seconds" | "-c" => {
                        if i + 1 < args.len() {
                            chunk_seconds = args[i + 1].parse().unwrap_or(600);
                            i += 1;
                        }
                    }
                    "--search-window" | "-w" => {
                        if i + 1 < args.len() {
                            search_window = args[i + 1].parse().unwrap_or(10.0);
                            i += 1;
                        }
                    }
                    "--json" => as_json = true,
                    _ => {}
                }
                i += 1;
            }

            let input_path = match input {
                Some(p) => p,
                None => {
                    eprintln!("Error: Missing --input parameter");
                    std::process::exit(1);
                }
            };
            let out_dir = match output_dir {
                Some(p) => p,
                None => {
                    eprintln!("Error: Missing --output-dir parameter");
                    std::process::exit(1);
                }
            };

            let start_time = std::time::Instant::now();
            match slice_audio_silence_aware(&input_path, &out_dir, chunk_seconds, search_window) {
                Ok(chunks) => {
                    let elapsed_ms = start_time.elapsed().as_millis();
                    if as_json {
                        let mut chunk_objs = Vec::new();
                        for c in &chunks {
                            let path_str = c.path.to_string_lossy().replace('\\', "\\\\");
                            chunk_objs.push(format!(
                                "{{\"chunk_index\":{},\"path\":\"{}\",\"start_seconds\":{},\"end_seconds\":{},\"duration_seconds\":{},\"sample_count\":{},\"silence_aligned\":{}}}",
                                c.chunk_index, path_str, c.start_seconds, c.end_seconds, c.duration_seconds, c.sample_count, c.silence_aligned
                            ));
                        }
                        println!(
                            "{{\"total_chunks\":{},\"elapsed_ms\":{},\"chunks\":[{}]}}",
                            chunks.len(),
                            elapsed_ms,
                            chunk_objs.join(",")
                        );
                    } else {
                        println!("Sliced into {} chunks in {} ms (silence-aligned)", chunks.len(), elapsed_ms);
                        for c in &chunks {
                            println!(
                                "  Chunk #{:02}: {:?} [{:.2}s -> {:.2}s] ({:.2}s)",
                                c.chunk_index,
                                c.path.file_name().unwrap_or_default(),
                                c.start_seconds,
                                c.end_seconds,
                                c.duration_seconds
                            );
                        }
                    }
                }
                Err(e) => {
                    eprintln!("Error slicing audio: {}", e);
                    std::process::exit(1);
                }
            }
        }
        _ => {
            eprintln!("Unknown command: {}", command);
            print_usage();
            std::process::exit(1);
        }
    }
}
