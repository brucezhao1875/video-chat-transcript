#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字幕合并与追踪工具

功能：
- 读取数据源csv（如ds_jietuoyuan.csv），自动识别三种语言（中/英/泰）字幕
- 按顺序每20个视频为一组，抓取YouTube字幕（用YouTubeTranscriptApi，支持zh/zh-Hans/zh-CN/zh-Hant/en/th等标签）
- 合并为.data文件，仿照字幕csv格式
- 追踪表csv，记录每个video_id、语言、合并到的数据文件名、处理时间
- 支持参数：最大抓取视频数（默认40，all为全部）
- 支持断点续传（已处理的video_id+语言组合自动跳过）
- 所有输出到data目录

用法示例：
  python subtitle_merger.py --source-csv ../data/ds_jietuoyuan.csv --group-size 20 --max-videos 40
  python subtitle_merger.py --source-csv ../data/ds_luangpupramote.csv --group-size 20 --max-videos all

依赖：
  pip install youtube-transcript-api chardet
"""
import os
import csv
import argparse
import time
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import chardet

DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
TRACKING_FILE = os.path.join(DATA_DIR, 'subtitle_merge_tracking.csv')

LANG_GROUPS = {
    'zh': ['zh', 'zh-Hans', 'zh-CN', 'zh-Hant', 'zh-TW', 'zh-HK'],
    'en': ['en', 'en-US', 'en-GB'],
    'th': ['th']
}
LANG_ORDER = ['zh', 'en', 'th']
FIELDNAMES = ['text', 'video_url', 'start_time_seconds', 'speaker']

def load_tracking():
    processed = set()
    table = []
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed.add((row['video_id'], row['lang']))
                table.append(row)
    return processed, table

def save_tracking(table):
    with open(TRACKING_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['video_id', 'lang', 'merged_file', 'processed_time']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in table:
            writer.writerow(row)

def get_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw = f.read(4096)
    result = chardet.detect(raw)
    encoding = result['encoding'] or 'utf-8'
    if encoding.lower() in ['gb2312', 'gb18030']:
        encoding = 'gbk'
    return encoding

def get_video_list(source_csv):
    """读取数据源csv，返回(video_id, title, url, subtitle)列表，最新在前（自动检测编码）"""
    videos = []
    encoding = get_file_encoding(source_csv)
    with open(source_csv, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            video_id = row.get('video_id') or row.get('id')
            title = row.get('title') or row.get('video_title')
            url = row.get('video_url') or f'https://www.youtube.com/watch?v={video_id}'
            subtitle = row.get('subtitle', '')
            if video_id:
                videos.append({'video_id': video_id, 'title': title, 'url': url, 'subtitle': subtitle})
    return videos

def fetch_transcript(video_id, lang_code):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
        return transcript
    except (NoTranscriptFound, TranscriptsDisabled):
        return None
    except Exception as e:
        print(f"[{video_id}] 抓取字幕失败: {e}")
        return None

def merge_and_save(group, lang, part_idx, source_name):
    merged_lines = []
    tracking_rows = []
    for v in group:
        video_id = v['video_id']
        url = v['url']
        speaker = '老师' if lang == 'zh' else ('Ajahn' if lang == 'th' else 'Speaker')
        transcript = fetch_transcript(video_id, lang_code=LANG_GROUPS[lang][0])
        if not transcript:
            print(f"[跳过] {video_id} 无{lang}字幕")
            continue
        for entry in transcript:
            merged_lines.append({
                'text': entry['text'],
                'video_url': url,
                'start_time_seconds': round(entry['start'], 2),
                'speaker': speaker
            })
        tracking_rows.append({
            'video_id': video_id,
            'lang': lang,
            'merged_file': f"{source_name}_{lang}_part{part_idx}.data",
            'processed_time': datetime.now().isoformat(timespec='seconds')
        })
    if merged_lines:
        out_path = os.path.join(DATA_DIR, f"{source_name}_{lang}_part{part_idx}.data")
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in merged_lines:
                writer.writerow(row)
        print(f"✅ 生成: {out_path} ({len(merged_lines)} 条字幕)")
    return tracking_rows

def main():
    parser = argparse.ArgumentParser(description="YouTube字幕批量抓取与合并工具")
    parser.add_argument('--source-csv', required=True, help='数据源csv路径')
    parser.add_argument('--group-size', type=int, default=20, help='每个数据文件包含视频数')
    parser.add_argument('--max-videos', default=40, help='最大抓取有字幕视频数，all为全部')
    parser.add_argument('--source-name', type=str, default=None, help='数据源名（如JieTuoYuan），默认取csv文件名')
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    processed, tracking_table = load_tracking()
    videos = get_video_list(args.source_csv)
    source_name = args.source_name or os.path.splitext(os.path.basename(args.source_csv))[0]

    # 统计每种语言可用视频（直接用subtitle字段判断）
    lang_video_lists = {lang: [] for lang in LANG_ORDER}
    count_per_lang = {lang: 0 for lang in LANG_ORDER}
    max_videos = None if args.max_videos == 'all' else int(args.max_videos)

    print(f"共{len(videos)}个视频，开始筛选可用字幕...")
    for v in videos:
        video_id = v['video_id']
        subtitle = v.get('subtitle', '')
        for lang in LANG_ORDER:
            if count_per_lang[lang] == max_videos:
                continue
            if (video_id, lang) in processed:
                continue  # 已处理
            if lang in subtitle.split(','):
                lang_video_lists[lang].append(v)
                count_per_lang[lang] += 1

    # 分组合并
    for lang in LANG_ORDER:
        group = []
        part_idx = 1
        for v in lang_video_lists[lang]:
            if (v['video_id'], lang) in processed:
                continue
            group.append(v)
            if len(group) == args.group_size:
                tracking_rows = merge_and_save(group, lang, part_idx, source_name)
                tracking_table.extend(tracking_rows)
                save_tracking(tracking_table)
                group = []
                part_idx += 1
        # 处理最后不足一组的
        if group:
            tracking_rows = merge_and_save(group, lang, part_idx, source_name)
            tracking_table.extend(tracking_rows)
            save_tracking(tracking_table)

if __name__ == '__main__':
    main()