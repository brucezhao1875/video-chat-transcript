#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YouTube字幕抓取与分块工具 (YouTube Subtitle Chunker)

功能:
  - 本脚本通过一个指定的YouTube视频URL，自动抓取其可用字幕。
  - 将连续的字幕条目按照用户设定的"最小时间"合并成更大的文本块 (chunk)。
  - 最终将处理好的数据（合并后的文本、视频URL、起始时间、演讲者）保存为CSV格式的文件。
  - 脚本支持灵活的命令行参数来自定义其行为。

=============================================================================
前置条件 (Prerequisites):
  1. 安装必要的第三方库:
     - 本脚本依赖 `youtube-transcript-api` 库来获取YouTube字幕。
     - 在首次运行脚本前，请打开您的终端或命令行工具，执行以下命令进行安装：

       pip install youtube-transcript-api
=============================================================================
使用方法 (Usage):
  在配置好前置条件后，于命令行中执行：

  1. 基本用法 (使用默认设置):
     python subtitle_chunker.py "https://www.youtube.com/watch?v=NcISDw5rzac"

  2. 自定义所有参数:
     python subtitle_chunker.py "https://www.youtube.com/watch?v=NcISDw5rzac" -t 60 -s "主讲人" -o "my_notes.csv"

  3. 查看帮助:
     python subtitle_chunker.py --help
=============================================================================
todo list：
  1. 增加语义判断的方法，将字幕分块，并判断是否需要合并.目前是按照时间分块，没有考虑语义
  2. 增加一个参数，用于指定字幕的语言
  3. 增加主讲人识别功能，使得主讲人可以被识别出来
"""
import argparse
import csv
import sys
import os
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled


def get_video_id(url: str) -> str | None:
    """
    (已简化) 从指定的URL格式中提取视频ID。
    预期格式: 'https://www.youtube.com/watch?v=NcISDw5rzac'
    """
    if not url:
        return None
    try:
        # 解析URL并提取查询参数
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # 视频ID被假定为 'v' 查询参数的值
        video_id = query_params.get('v', [None])[0]
        return video_id
    except (AttributeError, IndexError):
        # 如果URL格式不正确或缺少 'v' 参数，则返回None
        return None

def chunk_transcript(transcript: list[dict], min_chunk_time: float) -> list[dict]:
    """
    将原始字幕列表合并成按时间分块的列表。

    Args:
        transcript: 从API获取的原始字幕列表。
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
        # 累加每个字幕段的实际持续时间
        current_chunk_duration += item['duration']

        # 如果当前分块的累积时长已达到或超过最小要求
        if current_chunk_duration >= min_chunk_time:
            # 合并文本并创建分块
            full_text = " ".join(current_chunk_text)
            chunks.append({
                'text': full_text,
                'start_time': current_chunk_start_time
            })
            # 重置下一个分块
            current_chunk_text = []
            current_chunk_start_time = None
            current_chunk_duration = 0.0

    # 处理循环结束后剩余的最后一部分字幕
    if current_chunk_text:
        full_text = " ".join(current_chunk_text)
        chunks.append({
            'text': full_text,
            'start_time': current_chunk_start_time
        })

    print(f"⚙️字幕已处理成 {len(chunks)} 个分块。")
    return chunks

def save_to_csv(chunks: list[dict], output_file: str, video_url: str, speaker: str):
    """
    将分块后的字幕数据保存到CSV文件。
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            # utf-8-sig 编码可以帮助Excel正确识别UTF-8
            fieldnames = ['text', 'video_url', 'start_time_seconds', 'speaker']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for chunk in chunks:
                writer.writerow({
                    'text': chunk['text'],
                    'video_url': video_url,
                    'start_time_seconds': round(chunk['start_time'], 2), # 保留两位小数
                    'speaker': speaker
                })
        print(f"💾成功保存到文件: {output_file}")
    except IOError as e:
        print(f"❌错误：无法写入文件 {output_file}。原因: {e}", file=sys.stderr)


def main():
    """主函数，用于解析参数和协调整个流程。"""
    parser = argparse.ArgumentParser(
        description="从YouTube视频抓取字幕，合并成段落(chunk)，并存为CSV文件。",
        formatter_class=argparse.RawTextHelpFormatter # 保持帮助信息格式
    )
    parser.add_argument(
        "youtube_url", 
        help="目标YouTube视频的URL。\n格式应为: 'https://www.youtube.com/watch?v=NcISDw5rzac'"
    )
    parser.add_argument(
        "-t", "--min_chunk_time", 
        type=float, 
        default=45.0, 
        help="每个字幕块的最小合并时间（秒）。\n缺省值: 45.0"
    )
    parser.add_argument(
        "-s", "--speaker", 
        type=str, 
        default="老师", 
        help="演讲者的名字。\n缺省值: '老师'"
    )
    parser.add_argument(
        "-o", "--output_file", 
        type=str, 
        help="输出的CSV文件名。\n缺省: <video_id>_<lang>.csv"
    )

    args = parser.parse_args()

    # 1. 获取视频ID
    video_id = get_video_id(args.youtube_url)
    if not video_id:
        print(f"❌错误：无法从URL '{args.youtube_url}' 中解析出视频ID。\n请确保URL格式正确并包含 'v' 参数，例如：'https://www.youtube.com/watch?v=NcISDw5rzac'。", file=sys.stderr)
        sys.exit(1)
    
    print(f"🎬解析视频ID: {video_id}")

    # 2. 获取字幕
    preferred_languages = ['zh-Hans', 'zh-CN', 'zh']
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred_languages)
        lang_code = transcript[0].get('lang', 'unknown') if transcript else 'unknown'
        print(f"✅成功获取字幕，语言: {lang_code}")
    except TranscriptsDisabled:
        print(f"❌错误：视频 '{video_id}' 已禁用字幕。", file=sys.stderr)
        sys.exit(1)
    except NoTranscriptFound:
        print(f"❌错误：视频 '{video_id}' 没有找到任何可用字幕。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌发生未知错误: {str(e)}", file=sys.stderr)
        print(f"错误类型: {type(e).__name__}", file=sys.stderr)
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

    # 3. 合并成块
    chunks = chunk_transcript(transcript, args.min_chunk_time)
    if not chunks:
        print("⚠️警告：未能生成任何字幕分块。")
        sys.exit(1)

    # 4. 确定输出文件名
    output_file = args.output_file
    if not output_file:
        output_file = f"{video_id}_{lang_code}.csv"

    # 5. 保存到CSV
    save_to_csv(chunks, output_file, args.youtube_url, args.speaker)


if __name__ == "__main__":
    main()