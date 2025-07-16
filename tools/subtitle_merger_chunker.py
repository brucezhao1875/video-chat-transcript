#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 subtitle_merger.py 生成的 .data 字幕文件，按视频分组并合并为更长的段落（chunk），便于知识库加载。
"""
import argparse
import csv
import os
from collections import defaultdict
from typing import List, Dict

def chunk_transcript(transcript: List[Dict], min_chunk_time: float) -> List[Dict]:
    """
    将原始字幕列表合并成按时间分块的列表。
    Args:
        transcript: 原始字幕列表（每条含 text, start, duration）。
        min_chunk_time: 每个分块的最小秒数。
    Returns:
        一个包含分块后字幕的字典列表。
    """
    chunks = []
    current_chunk_text = []
    current_chunk_start_time = None
    current_chunk_duration = 0.0
    if not transcript:
        return []
    for item in transcript:
        if current_chunk_start_time is None:
            current_chunk_start_time = item['start']
        current_chunk_text.append(item['text'])
        current_chunk_duration += item['duration']
        if current_chunk_duration >= min_chunk_time:
            full_text = " ".join(current_chunk_text)
            chunks.append({
                'text': full_text,
                'start_time': current_chunk_start_time
            })
            current_chunk_text = []
            current_chunk_start_time = None
            current_chunk_duration = 0.0
    if current_chunk_text:
        full_text = " ".join(current_chunk_text)
        chunks.append({
            'text': full_text,
            'start_time': current_chunk_start_time
        })
    return chunks

def read_merger_data(file_path: str) -> List[Dict]:
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def build_transcript(rows: List[Dict]) -> List[Dict]:
    transcript = []
    for i, row in enumerate(rows):
        start = float(row['start_time_seconds'])
        if i < len(rows) - 1:
            duration = float(rows[i+1]['start_time_seconds']) - start
            if duration <= 0:
                duration = 2.0
        else:
            duration = 2.0
        transcript.append({'text': row['text'], 'start': start, 'duration': duration})
    return transcript

def save_chunks_to_csv(chunks: List[Dict], output_file: str, video_url: str, speaker: str):
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['text', 'video_url', 'start_time_seconds', 'speaker']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for chunk in chunks:
            writer.writerow({
                'text': chunk['text'],
                'video_url': video_url,
                'start_time_seconds': round(chunk['start_time'], 2),
                'speaker': speaker
            })

def main():
    parser = argparse.ArgumentParser(description="将 merger 生成的字幕文件按视频分组并分块合并。")
    parser.add_argument('--input-file', required=True, help='.data 字幕文件路径')
    parser.add_argument('--min-chunk-time', type=float, default=45.0, help='每个 chunk 的最小秒数，默认45')
    parser.add_argument('--output-dir', type=str, default='.', help='输出目录，默认当前目录')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    rows = read_merger_data(args.input_file)
    if not rows:
        print(f"未读取到任何字幕数据: {args.input_file}")
        return
    # 按 video_url 分组
    video_groups = defaultdict(list)
    for row in rows:
        video_groups[row['video_url']].append(row)
    # 获取原始文件名（不含扩展名）
    base_name = os.path.splitext(os.path.basename(args.input_file))[0]
    all_chunks = []
    for video_url, group_rows in video_groups.items():
        # 按 start_time_seconds 排序
        group_rows.sort(key=lambda r: float(r['start_time_seconds']))
        transcript = build_transcript(group_rows)
        chunks = chunk_transcript(transcript, args.min_chunk_time)
        if not chunks:
            print(f"视频 {video_url} 未生成任何 chunk，跳过。")
            continue
        # 取 video_id
        video_id = None
        # 尝试从 url 提取 v=xxx
        import re
        m = re.search(r'v=([\w-]+)', video_url)
        if m:
            video_id = m.group(1)
        else:
            video_id = video_url[-11:]  # fallback
        speaker = group_rows[0].get('speaker', '')
        for chunk in chunks:
            all_chunks.append({
                'text': chunk['text'],
                'video_url': video_url,
                'start_time_seconds': round(chunk['start_time'], 2),
                'speaker': speaker
            })
    # 输出到一个文件
    output_file = os.path.join(
        args.output_dir,
        f"{base_name}_chunk{int(args.min_chunk_time)}s.csv"
    )
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['text', 'video_url', 'start_time_seconds', 'speaker']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_chunks:
            writer.writerow(row)
    print(f"✅ 已生成: {output_file}（共 {len(all_chunks)} 段）")

if __name__ == "__main__":
    main() 