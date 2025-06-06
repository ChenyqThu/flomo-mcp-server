#!/usr/bin/env python3

import requests
import hashlib
import json
from datetime import datetime
from bs4 import BeautifulSoup
from html2text import html2text
import time

class FlomoSearchAPI:
    def __init__(self, token):
        self.token = token
        self.salt = "dbbc3dd73364b4084c3a69346e0ce2b2"
        self.base_url = "https://flomoapp.com/api/v1/memo/updated/"
        
    def _generate_params(self, extra_params=None):
        """生成API参数和签名"""
        params = {
            "timestamp": str(int(datetime.now().timestamp())),
            "api_key": "flomo_web",
            "app_version": "4.0",
            "platform": "web",
            "webp": "1"
        }
        
        if extra_params:
            params.update(extra_params)
        
        # 生成签名
        param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        sign = hashlib.md5((param_str + self.salt).encode("utf-8")).hexdigest()
        params["sign"] = sign
        
        return params
    
    def search(self, query, limit=50):
        """
        搜索备忘录
        
        Args:
            query: 搜索关键词
            limit: 结果数量限制（实际返回数量可能少于此值）
        
        Returns:
            搜索结果列表
        """
        if not query.strip():
            return []
        
        try:
            params = self._generate_params({
                "q": query,
                "limit": str(limit)
            })
            
            headers = {"Authorization": self.token}
            
            print(f"🔍 搜索关键词: '{query}'")
            print(f"📊 请求参数: {params}")
            
            response = requests.get(self.base_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    results = data.get("data", [])
                    print(f"✅ 搜索成功，找到 {len(results)} 条结果")
                    return results
                else:
                    print(f"❌ API错误: {data.get('message')}")
                    return []
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"💥 搜索异常: {e}")
            return []
    
    def search_with_pagination(self, query, max_results=200):
        """
        支持分页的搜索（获取更多结果）
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数量
        """
        all_results = []
        latest_slug = None
        latest_updated_at = None
        page = 1
        
        while len(all_results) < max_results:
            try:
                search_params = {"q": query, "limit": "50"}
                
                # 添加分页参数
                if latest_slug and latest_updated_at:
                    search_params.update({
                        "latest_slug": latest_slug,
                        "latest_updated_at": str(latest_updated_at)
                    })
                
                params = self._generate_params(search_params)
                headers = {"Authorization": self.token}
                
                print(f"🔍 搜索第 {page} 页: '{query}'")
                
                response = requests.get(self.base_url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 0:
                        results = data.get("data", [])
                        
                        if not results:
                            break
                        
                        all_results.extend(results)
                        print(f"📄 第 {page} 页获取 {len(results)} 条结果")
                        
                        # 如果这页结果少于50条，说明没有更多数据了
                        if len(results) < 50:
                            break
                        
                        # 设置下一页参数
                        last_memo = results[-1]
                        latest_slug = last_memo["slug"]
                        latest_updated_at = int(datetime.fromisoformat(last_memo["updated_at"]).timestamp())
                        
                        page += 1
                        time.sleep(0.5)  # 避免请求过快
                    else:
                        print(f"❌ API错误: {data.get('message')}")
                        break
                else:
                    print(f"❌ HTTP错误: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"💥 搜索异常: {e}")
                break
        
        print(f"✅ 搜索完成，总共找到 {len(all_results)} 条结果")
        return all_results[:max_results]
    
    def parse_search_result(self, memo):
        """解析搜索结果"""
        content = memo.get('content', '')
        
        # 转换HTML为文本
        soup = BeautifulSoup(content, 'html.parser')
        plain_text = soup.get_text(separator='\n', strip=True)
        markdown_text = html2text(content).strip()
        
        # 提取标签
        import re
        tags = re.findall(r'#([^\s#]+)', content)
        
        # 文件信息
        files = memo.get('files', [])
        file_info = []
        for file_item in files:
            file_info.append({
                'id': file_item.get('id'),
                'type': file_item.get('type'),
                'name': file_item.get('name'),
                'size': file_item.get('size')
            })
        
        return {
            'slug': memo.get('slug'),
            'created_at': memo.get('created_at'),
            'updated_at': memo.get('updated_at'),
            'creator_id': memo.get('creator_id'),
            'source': memo.get('source'),
            'pin': memo.get('pin'),
            'linked_count': memo.get('linked_count'),
            'original_html': content,
            'plain_text': plain_text,
            'markdown': markdown_text,
            'tags': tags,
            'files': file_info,
            'has_files': len(files) > 0,
            'word_count': len(plain_text),
            'url': f"https://v.flomoapp.com/mine/?memo_id={memo.get('slug')}"
        }
    
    def advanced_search(self, query, include_tags=None, exclude_tags=None, 
                       has_files=None, date_from=None, date_to=None):
        """
        高级搜索（在搜索结果基础上进行过滤）
        
        Args:
            query: 基础搜索关键词
            include_tags: 必须包含的标签列表
            exclude_tags: 必须排除的标签列表  
            has_files: True=只要有文件的, False=只要没文件的, None=不限制
            date_from: 开始日期 (datetime对象)
            date_to: 结束日期 (datetime对象)
        """
        # 先进行基础搜索
        base_results = self.search_with_pagination(query, max_results=500)
        
        if not base_results:
            return []
        
        # 解析所有结果
        parsed_results = [self.parse_search_result(memo) for memo in base_results]
        
        # 应用过滤条件
        filtered_results = []
        
        for result in parsed_results:
            # 标签过滤
            if include_tags:
                if not all(tag in result['tags'] for tag in include_tags):
                    continue
            
            if exclude_tags:
                if any(tag in result['tags'] for tag in exclude_tags):
                    continue
            
            # 文件过滤
            if has_files is not None:
                if has_files and not result['has_files']:
                    continue
                elif not has_files and result['has_files']:
                    continue
            
            # 日期过滤
            if date_from or date_to:
                try:
                    memo_date = datetime.fromisoformat(result['created_at'].replace('Z', '+00:00'))
                    if date_from and memo_date < date_from:
                        continue
                    if date_to and memo_date > date_to:
                        continue
                except:
                    continue
            
            filtered_results.append(result)
        
        print(f"🎯 高级搜索完成，从 {len(parsed_results)} 条结果中筛选出 {len(filtered_results)} 条")
        return filtered_results
    
    def get_file_details(self, file_ids):
        """
        获取文件详细信息
        
        Args:
            file_ids: 文件ID列表
        """
        if not file_ids:
            return []
        
        try:
            # 构建文件API参数
            file_params = {}
            for i, file_id in enumerate(file_ids):
                file_params[f"ids[{i}]"] = str(file_id)
            
            params = self._generate_params(file_params)
            headers = {"Authorization": self.token}
            
            response = requests.get(
                "https://flomoapp.com/api/v1/file/",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    return data.get("data", [])
            
            return []
            
        except Exception as e:
            print(f"💥 获取文件信息失败: {e}")
            return []

def demo_search_functionality():
    """演示搜索功能"""
    # 配置token
    TOKEN = "Bearer 6782846|pguJkOHgJ21KYW4oHfrEF0syJvHRygKI5a53Mitf"
    
    search_api = FlomoSearchAPI(TOKEN)
    
    print("🚀 Flomo 搜索功能演示")
    print("="*60)
    
    # 1. 基础搜索
    print("\n1️⃣ 基础搜索演示")
    results = search_api.search("夕阳", limit=10)
    
    if results:
        print(f"📋 搜索结果预览:")
        for i, memo in enumerate(results[:3], 1):
            parsed = search_api.parse_search_result(memo)
            print(f"\n   {i}. [{parsed['created_at']}]")
            print(f"      内容: {parsed['plain_text'][:80]}...")
            print(f"      标签: {parsed['tags']}")
            print(f"      文件: {len(parsed['files'])} 个")
            print(f"      链接: {parsed['url']}")
    
    # 2. 分页搜索
    print(f"\n2️⃣ 分页搜索演示（获取更多结果）")
    all_results = search_api.search_with_pagination("夕阳", max_results=100)
    print(f"📊 总搜索结果: {len(all_results)} 条")
    
    # 3. 高级搜索
    print(f"\n3️⃣ 高级搜索演示")
    from datetime import datetime, timedelta
    
    # 搜索最近30天包含"夕阳"且有文件的备忘录
    date_from = datetime.now() - timedelta(days=30)
    advanced_results = search_api.advanced_search(
        query="夕阳",
        has_files=True,
        date_from=date_from
    )
    
    print(f"📸 最近30天包含'夕阳'且有图片的备忘录: {len(advanced_results)} 条")
    
    # 4. 获取文件信息
    if advanced_results:
        first_result = advanced_results[0]
        if first_result['files']:
            file_ids = [f['id'] for f in first_result['files']]
            file_details = search_api.get_file_details(file_ids)
            print(f"📁 文件详情: {len(file_details)} 个文件")
            
            for file_detail in file_details[:2]:  # 显示前2个文件
                print(f"   - {file_detail.get('name')} ({file_detail.get('size')} bytes)")
                print(f"     图片URL: {file_detail.get('url')}")
    
    print(f"\n🎉 搜索功能演示完成！")

if __name__ == "__main__":
    demo_search_functionality()