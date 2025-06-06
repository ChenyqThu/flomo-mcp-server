#!/usr/bin/env python3

import requests
import hashlib
import json
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from html2text import html2text
import os
from collections import Counter

class FlomoAnalyzer:
    def __init__(self, token):
        self.token = token
        self.salt = "dbbc3dd73364b4084c3a69346e0ce2b2"
        self.base_url = "https://flomoapp.com/api/v1/memo/updated/"
        
    def get_memos_page(self, latest_slug=None, latest_updated_at=None, limit=200):
        """获取一页备忘录数据"""
        current_timestamp = str(int(datetime.now().timestamp()))
        
        params = {
            "limit": str(limit),
            "tz": "8:0", 
            "timestamp": current_timestamp,
            "api_key": "flomo_web",
            "app_version": "4.0",
            "platform": "web",
            "webp": "1"
        }
        
        if latest_slug and latest_updated_at:
            params.update({
                "latest_slug": latest_slug,
                "latest_updated_at": str(latest_updated_at)
            })
        
        # 生成签名
        param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        sign = hashlib.md5((param_str + self.salt).encode("utf-8")).hexdigest()
        params["sign"] = sign
        
        headers = {"Authorization": self.token}
        
        try:
            response = requests.get(self.base_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    return data.get("data", [])
            return None
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    def get_all_memos(self):
        """获取所有备忘录"""
        all_memos = []
        latest_slug = None
        latest_updated_at = None
        page = 1
        
        while True:
            print(f"正在获取第 {page} 页数据...")
            memos = self.get_memos_page(latest_slug, latest_updated_at)
            
            if not memos:
                break
                
            all_memos.extend(memos)
            print(f"第 {page} 页获取到 {len(memos)} 条备忘录")
            
            if len(memos) < 200:  # 最后一页
                break
                
            # 设置下一页参数
            last_memo = memos[-1]
            latest_slug = last_memo["slug"]
            latest_updated_at = int(datetime.fromisoformat(last_memo["updated_at"]).timestamp())
            page += 1
        
        print(f"✅ 总共获取到 {len(all_memos)} 条备忘录")
        return all_memos
    
    def parse_memo_content(self, memo):
        """解析备忘录内容"""
        content = memo.get('content', '')
        
        # 转换为纯文本
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        
        # 转换为 Markdown
        markdown = html2text(content).strip()
        
        return {
            'slug': memo.get('slug'),
            'created_at': memo.get('created_at'),
            'updated_at': memo.get('updated_at'),
            'original_html': content,
            'plain_text': text,
            'markdown': markdown,
            'word_count': len(text),
            'tags': self.extract_tags(content)
        }
    
    def extract_tags(self, content):
        """提取标签"""
        import re
        # 提取 #标签
        tags = re.findall(r'#([^\s#]+)', content)
        return tags
    
    def analyze_memos(self, memos):
        """分析备忘录数据"""
        parsed_memos = [self.parse_memo_content(memo) for memo in memos]
        
        # 统计信息
        total_count = len(parsed_memos)
        total_words = sum(memo['word_count'] for memo in parsed_memos)
        
        # 按年月统计
        date_counter = Counter()
        tag_counter = Counter()
        
        for memo in parsed_memos:
            if memo['created_at']:
                date = memo['created_at'][:7]  # YYYY-MM
                date_counter[date] += 1
            
            for tag in memo['tags']:
                tag_counter[tag] += 1
        
        # 时间范围
        dates = [memo['created_at'] for memo in parsed_memos if memo['created_at']]
        earliest = min(dates) if dates else "N/A"
        latest = max(dates) if dates else "N/A"
        
        analysis = {
            'total_memos': total_count,
            'total_words': total_words,
            'avg_words_per_memo': round(total_words / total_count, 2) if total_count > 0 else 0,
            'date_range': f"{earliest} 到 {latest}",
            'monthly_distribution': dict(date_counter.most_common()),
            'top_tags': dict(tag_counter.most_common(20)),
            'parsed_memos': parsed_memos
        }
        
        return analysis
    
    def export_to_csv(self, analysis, filename="flomo_export.csv"):
        """导出到CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['slug', 'created_at', 'updated_at', 'plain_text', 'markdown', 'word_count', 'tags']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for memo in analysis['parsed_memos']:
                writer.writerow({
                    'slug': memo['slug'],
                    'created_at': memo['created_at'],
                    'updated_at': memo['updated_at'],
                    'plain_text': memo['plain_text'],
                    'markdown': memo['markdown'],
                    'word_count': memo['word_count'],
                    'tags': ','.join(memo['tags'])
                })
        
        print(f"✅ 数据已导出到 {filename}")
    
    def export_to_json(self, analysis, filename="flomo_export.json"):
        """导出到JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据已导出到 {filename}")
    
    def print_analysis(self, analysis):
        """打印分析结果"""
        print(f"\n{'='*60}")
        print(f"📊 Flomo 数据分析报告")
        print(f"{'='*60}")
        print(f"📝 总备忘录数量: {analysis['total_memos']:,}")
        print(f"📖 总字数: {analysis['total_words']:,}")
        print(f"📄 平均每条字数: {analysis['avg_words_per_memo']}")
        print(f"📅 时间范围: {analysis['date_range']}")
        
        print(f"\n🏷️  热门标签 (Top 10):")
        for tag, count in list(analysis['top_tags'].items())[:10]:
            print(f"   #{tag}: {count} 次")
        
        print(f"\n📈 月度分布 (Top 10):")
        for month, count in list(analysis['monthly_distribution'].items())[:10]:
            print(f"   {month}: {count} 条")
        
        print(f"\n💡 最新的 5 条备忘录:")
        latest_memos = sorted(analysis['parsed_memos'], 
                            key=lambda x: x['created_at'] or '', reverse=True)[:5]
        for i, memo in enumerate(latest_memos, 1):
            preview = memo['plain_text'][:100] + "..." if len(memo['plain_text']) > 100 else memo['plain_text']
            print(f"   {i}. [{memo['created_at']}] {preview}")

def main():
    # 配置你的token
    TOKEN = "Bearer 6782846|pguJkOHgJ21KYW4oHfrEF0syJvHRygKI5a53Mitf"
    
    analyzer = FlomoAnalyzer(TOKEN)
    
    print("🚀 开始获取和分析 Flomo 数据...")
    
    # 获取所有备忘录
    memos = analyzer.get_all_memos()
    
    if not memos:
        print("❌ 未能获取到数据")
        return
    
    # 分析数据
    print("\n📊 正在分析数据...")
    analysis = analyzer.analyze_memos(memos)
    
    # 显示分析结果
    analyzer.print_analysis(analysis)
    
    # 导出数据
    print(f"\n💾 正在导出数据...")
    analyzer.export_to_csv(analysis)
    analyzer.export_to_json(analysis)
    
    print(f"\n🎉 完成！你的 Flomo 数据已成功分析并导出。")

if __name__ == "__main__":
    main()