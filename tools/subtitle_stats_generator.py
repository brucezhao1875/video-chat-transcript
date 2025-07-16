#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字幕统计与元数据生成脚本

功能：
- 输入：原始视频列表csv（含video_id、title、url等）
- 对每个视频，远程检测所有可用字幕语言（用YouTubeTranscriptApi.list_transcripts）
- 生成/更新csv，增加subtitle字段（如zh,en,th）
- 输出：如ds_jietuoyuan.csv，含subtitle字段
- 支持自动检测输入文件编码，输出为utf-8
- 支持进度输出

用法示例：
  python subtitle_stats_generator.py --input-csv ../data/video_list.csv --output-csv ../data/ds_jietuoyuan.csv

依赖：
  pip install youtube-transcript-api chardet
"""
import os
import csv
import argparse
import chardet
from youtube_transcript_api import YouTubeTranscriptApi

def get_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw = f.read(4096)
    result = chardet.detect(raw)
    encoding = result['encoding'] or 'utf-8'
    if encoding.lower() in ['gb2312', 'gb18030']:
        encoding = 'gbk'
    return encoding

def detect_subtitles(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        langs = [t.language_code for t in transcript_list]
        # 归一化为zh/en/th三类
        lang_set = set()
        for code in langs:
            if code.startswith('zh'):
                lang_set.add('zh')
            elif code.startswith('en'):
                lang_set.add('en')
            elif code.startswith('th'):
                lang_set.add('th')
        return ','.join(sorted(lang_set))
    except Exception as e:
        return ''

def main():
    parser = argparse.ArgumentParser(description="YouTube字幕统计与元数据生成脚本")
    parser.add_argument('--input-csv', required=True, help='原始视频列表csv路径')
    parser.add_argument('--output-csv', required=True, help='输出csv路径（含subtitle字段）')
    args = parser.parse_args()

    encoding = get_file_encoding(args.input_csv)
    with open(args.input_csv, 'r', encoding=encoding) as fin:
        reader = csv.DictReader(fin)
        rows = list(reader)

    out_rows = []
    for idx, row in enumerate(rows, 1):
        video_id = row.get('video_id') or row.get('id')
        if not video_id:
            continue
        subtitle = detect_subtitles(video_id)
        row['subtitle'] = subtitle
        out_rows.append(row)
        print(f"[{idx}/{len(rows)}] {video_id} -> {subtitle}")

    fieldnames = list(out_rows[0].keys()) if out_rows else []
    with open(args.output_csv, 'w', newline='', encoding='utf-8') as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for row in out_rows:
            writer.writerow(row)
    print(f"✅ 已生成: {args.output_csv}，共{len(out_rows)}条")

if __name__ == '__main__':
    main() 