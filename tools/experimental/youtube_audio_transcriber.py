#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频转录与多语言识别工具

功能:
  - 支持YouTube视频URL或本地音频文件作为输入。
  - 如果是YouTube URL，自动下载音频；如果是本地文件，直接使用。
  - 用faster-whisper模型识别音频，逐句输出文本和起始时间。
  - 用langdetect识别每句语言（仅限中文、英文、泰文）。
  - 支持自定义Whisper模型大小和initial_prompt。
  - 结果保存为CSV，字段为text、start_time_seconds、language。
  - 自动清理临时音频文件（仅YouTube下载）。
  - 文件名自动添加时间戳，避免重复覆盖。

依赖:
  pip install yt-dlp faster-whisper langdetect

用法:
  # YouTube视频
  python youtube_audio_transcriber.py "https://www.youtube.com/watch?v=NcISDw5rzac"
  
  # 本地音频文件
  python youtube_audio_transcriber.py "audio.mp3"
  
  # 自定义参数
  python youtube_audio_transcriber.py "audio.mp3" -m large -p "This is a technical discussion"
"""
import argparse
import os
import sys
import subprocess
import csv
import tempfile
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from langdetect import detect
from faster_whisper import WhisperModel
import pathlib

LANG_MAP = {
    'zh-cn': 'zh', 'zh-tw': 'zh', 'zh': 'zh',
    'en': 'en',
    'th': 'th',
}

def normalize_lang(text):
    try:
        lang = detect(text)
        if lang.startswith('zh'):
            return 'zh'
        elif lang.startswith('en'):
            return 'en'
        elif lang.startswith('th'):
            return 'th'
        else:
            return 'unknown'
    except Exception:
        return 'unknown'

def is_youtube_url(input_path: str) -> bool:
    """判断输入是否为YouTube URL"""
    if not input_path:
        return False
    try:
        parsed = urlparse(input_path)
        return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be']
    except:
        return False

def get_video_id(url: str) -> str | None:
    if not url:
        return None
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get('v', [None])[0]
        return video_id
    except (AttributeError, IndexError):
        return None

def download_audio(youtube_url: str, output_dir: str) -> str:
    """下载YouTube音频，返回音频文件路径"""
    print("🎵 正在下载音频...")
    cmd = [
        'yt-dlp',
        '-f', 'bestaudio',
        '--extract-audio',
        '--audio-format', 'm4a',
        '-o', os.path.join(output_dir, '%(id)s.%(ext)s'),
        youtube_url
    ]
    subprocess.run(cmd, check=True)
    video_id = get_video_id(youtube_url)
    audio_path = os.path.join(output_dir, f"{video_id}.m4a")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件未找到: {audio_path}")
    print(f"✅ 音频已保存: {audio_path}")
    return audio_path

def transcribe_audio(audio_path: str, model_size: str = "small", initial_prompt: str = None) -> list:
    """
    用faster-whisper转录音频，返回句子列表（含文本和时间戳）。
    
    参数:
        audio_path: 音频文件路径
        model_size: Whisper模型大小 (tiny, base, small, medium, large)
        initial_prompt: 初始提示，用于指导转录
    """
    print("📝 正在识别音频...")
    print(f"🔧 使用模型: {model_size}")
    if initial_prompt:
        print(f"💡 使用提示: {initial_prompt}")
    
    model = WhisperModel(model_size, device="auto", compute_type="auto")
    
    # 转录参数
    transcribe_kwargs = {
        'beam_size': 5,
        'language': None,  # 让模型自动处理多语言
        'word_timestamps': False
    }
    
    # 如果提供了initial_prompt，添加到参数中
    if initial_prompt:
        transcribe_kwargs['initial_prompt'] = initial_prompt
    
    segments, info = model.transcribe(audio_path, **transcribe_kwargs)
    
    # 显示检测信息
    if hasattr(info, 'language') and info.language:
        print(f"Whisper检测到的主要语言: {info.language}")
    
    results = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            results.append({
                'text': text,
                'start': seg.start
            })
    print(f"✅ 识别完成，共 {len(results)} 句。")
    return results

def generate_filename_with_timestamp(base_name: str, model_size: str = "", initial_prompt: str = "") -> str:
    """
    生成带时间戳的文件名
    
    参数:
        base_name: 基础文件名（不含扩展名）
        model_size: 模型大小
        initial_prompt: 初始提示（用于区分不同参数）
    
    返回:
        格式化的文件名，如: "video_id_20231201_143022_small.csv"
    """
    # 获取当前时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 构建文件名
    filename_parts = [base_name, timestamp]
    
    # 添加模型大小信息
    if model_size and model_size != "small":  # small是默认值，不显示
        filename_parts.append(model_size)
    
    # 如果有initial_prompt，添加简化的标识
    if initial_prompt:
        # 取prompt的前几个字符作为标识
        prompt_id = initial_prompt[:10].replace(" ", "_").replace("'", "").replace('"', "")
        if len(prompt_id) > 0:
            filename_parts.append(f"prompt_{prompt_id}")
    
    # 组合文件名
    filename = "_".join(filename_parts) + ".csv"
    return filename

def save_to_csv(transcripts: list, output_file: str):
    """将转录结果保存为CSV文件"""
    # 确保data目录存在
    data_dir = pathlib.Path('data')
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / output_file
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['text', 'start_time_seconds', 'language']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in transcripts:
            writer.writerow(item)
    print(f"💾 已保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="音频转录与多语言识别工具")
    parser.add_argument("input", help="YouTube视频URL或本地音频文件路径")
    parser.add_argument("-o", "--output_file", type=str, help="输出CSV文件名（可选，默认自动生成带时间戳的文件名）")
    parser.add_argument("-m", "--model_size", type=str, default="small", 
                       help="Whisper模型大小（tiny, base, small, medium, large）")
    parser.add_argument("-p", "--initial_prompt", type=str, default="", 
                       help="初始提示，用于指导转录（如：'This is a Chinese-English mixed conversation'）")
    args = parser.parse_args()

    # 判断输入类型
    is_youtube = is_youtube_url(args.input)
    
    if is_youtube:
        # YouTube URL处理
        video_id = get_video_id(args.input)
        if not video_id:
            print("❌ 无法解析视频ID", file=sys.stderr)
            sys.exit(1)
        
        print(f"🎬 检测到YouTube视频: {video_id}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                audio_path = download_audio(args.input, tmpdir)
                segments = transcribe_audio(audio_path, args.model_size, args.initial_prompt)
                transcripts = []
                for seg in segments:
                    lang = normalize_lang(seg['text'])
                    if lang not in ('zh', 'en', 'th'):
                        lang = 'unknown'
                    transcripts.append({
                        'text': seg['text'],
                        'start_time_seconds': round(seg['start'], 2),
                        'language': lang
                    })
                
                # 生成输出文件名
                if args.output_file:
                    output_file = args.output_file
                else:
                    output_file = generate_filename_with_timestamp(
                        f"{video_id}_transcript", 
                        args.model_size, 
                        args.initial_prompt
                    )
                
                save_to_csv(transcripts, output_file)
            except Exception as e:
                print(f"❌ 错误: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        # 本地音频文件处理
        if not os.path.exists(args.input):
            print(f"❌ 音频文件不存在: {args.input}", file=sys.stderr)
            sys.exit(1)
        
        print(f"🎵 使用本地音频文件: {args.input}")
        
        try:
            segments = transcribe_audio(args.input, args.model_size, args.initial_prompt)
            transcripts = []
            for seg in segments:
                lang = normalize_lang(seg['text'])
                if lang not in ('zh', 'en', 'th'):
                    lang = 'unknown'
                transcripts.append({
                    'text': seg['text'],
                    'start_time_seconds': round(seg['start'], 2),
                    'language': lang
                })
            
            # 生成输出文件名
            if args.output_file:
                output_file = args.output_file
            else:
                # 使用输入文件名作为基础
                base_name = os.path.splitext(os.path.basename(args.input))[0]
                output_file = generate_filename_with_timestamp(
                    f"{base_name}_transcript", 
                    args.model_size, 
                    args.initial_prompt
                )
            
            save_to_csv(transcripts, output_file)
        except Exception as e:
            print(f"❌ 错误: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main() 