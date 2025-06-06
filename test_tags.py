#!/usr/bin/env python3

import requests
import hashlib
import json
from datetime import datetime
import time

class FlomoTagEnhancedTest:
    def __init__(self, token):
        self.token = token
        self.salt = "dbbc3dd73364b4084c3a69346e0ce2b2"
        self.base_url = "https://flomoapp.com/api/v1"
        
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
    
    def test_different_tag_endpoints(self):
        """测试不同的标签端点"""
        endpoints_to_test = [
            "/tag/updated/",
            "/tag/",
            "/tag/list/",
            "/tag/all/",
            "/tags/",
            "/tags/updated/",
            "/tags/list/",
            "/memo/tags/",
        ]
        
        headers = {"Authorization": self.token}
        results = {}
        
        print("🔍 测试不同的标签端点...")
        print("=" * 60)
        
        for endpoint in endpoints_to_test:
            print(f"\n📍 测试端点: {endpoint}")
            
            try:
                params = self._generate_params({"limit": "200", "tz": "8:0"})
                url = self.base_url + endpoint
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                print(f"   📊 状态码: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        api_code = data.get("code")
                        print(f"   ✅ API码: {api_code}")
                        
                        if api_code == 0:
                            tag_data = data.get("data", [])
                            print(f"   🎯 获取到 {len(tag_data)} 个标签")
                            
                            if tag_data:
                                first_item = tag_data[0] if isinstance(tag_data, list) else tag_data
                                if isinstance(first_item, dict):
                                    print(f"   📋 字段: {list(first_item.keys())}")
                                
                                results[endpoint] = {
                                    "success": True,
                                    "count": len(tag_data) if isinstance(tag_data, list) else 1,
                                    "sample": first_item,
                                    "data": tag_data
                                }
                        else:
                            print(f"   ❌ API错误: {data.get('message', 'Unknown')}")
                            results[endpoint] = {"success": False, "error": data.get('message')}
                    except json.JSONDecodeError:
                        print(f"   ❌ JSON解析失败")
                        results[endpoint] = {"success": False, "error": "JSON decode error"}
                else:
                    print(f"   ❌ HTTP错误: {response.status_code}")
                    results[endpoint] = {"success": False, "error": f"HTTP {response.status_code}"}
                    
            except requests.exceptions.Timeout:
                print(f"   ⏱️ 请求超时")
                results[endpoint] = {"success": False, "error": "Timeout"}
            except Exception as e:
                print(f"   💥 异常: {str(e)[:50]}...")
                results[endpoint] = {"success": False, "error": str(e)[:50]}
        
        return results
    
    def test_tag_pagination_deeply(self):
        """深度测试标签分页"""
        print("\n🔍 深度测试标签分页...")
        print("=" * 60)
        
        all_tags = []
        page = 1
        latest_updated_at = None
        
        # 测试多种分页参数组合
        pagination_strategies = [
            # 策略1: 基于 updated_at
            {"param": "latest_updated_at", "value": None},
            # 策略2: 基于 order
            {"param": "latest_order", "value": None},
            # 策略3: 基于 id
            {"param": "latest_id", "value": None},
            # 策略4: 使用 offset
            {"param": "offset", "value": 0},
            # 策略5: 使用 start_cursor
            {"param": "start_cursor", "value": None},
        ]
        
        for strategy in pagination_strategies:
            print(f"\n📋 测试分页策略: {strategy['param']}")
            
            try:
                # 重置分页参数
                page = 1
                strategy_tags = []
                param_value = strategy['value']
                
                while page <= 5:  # 最多测试5页
                    print(f"   第 {page} 页...")
                    
                    request_params = {"limit": "50", "tz": "8:0"}
                    
                    # 根据策略添加分页参数
                    if strategy['param'] == 'offset':
                        request_params['offset'] = str((page - 1) * 50)
                    elif param_value is not None:
                        request_params[strategy['param']] = str(param_value)
                    
                    params = self._generate_params(request_params)
                    headers = {"Authorization": self.token}
                    
                    response = requests.get(f"{self.base_url}/tag/updated/", 
                                          params=params, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("code") == 0:
                            tags = data.get("data", [])
                            print(f"     获取到 {len(tags)} 个标签")
                            
                            if not tags or len(tags) == 0:
                                print("     没有更多数据")
                                break
                            
                            strategy_tags.extend(tags)
                            
                            # 更新分页参数
                            if tags and strategy['param'] == 'latest_updated_at':
                                last_tag = tags[-1]
                                if 'updated_at' in last_tag:
                                    try:
                                        param_value = int(datetime.fromisoformat(last_tag['updated_at']).timestamp())
                                    except:
                                        print("     时间解析失败")
                                        break
                            elif tags and strategy['param'] == 'latest_id':
                                param_value = tags[-1].get('id')
                            elif tags and strategy['param'] == 'latest_order':
                                param_value = tags[-1].get('order')
                            
                            # 如果返回数据少于请求数量，说明已经是最后一页
                            if len(tags) < 50:
                                print("     已到达最后一页")
                                break
                        else:
                            print(f"     API错误: {data.get('message')}")
                            break
                    else:
                        print(f"     HTTP错误: {response.status_code}")
                        break
                    
                    page += 1
                    time.sleep(0.5)  # 避免请求过快
                
                print(f"   策略 {strategy['param']} 总共获取: {len(strategy_tags)} 个标签")
                
                if len(strategy_tags) > len(all_tags):
                    all_tags = strategy_tags
                    print(f"   ✅ 这是目前最好的策略！")
                
            except Exception as e:
                print(f"   💥 策略失败: {e}")
        
        print(f"\n🎯 最终结果: 获取到 {len(all_tags)} 个标签")
        return all_tags
    
    def analyze_tag_hierarchy(self, tags):
        """分析标签层级结构"""
        print("\n🔍 分析标签层级结构...")
        print("=" * 60)
        
        if not tags:
            return None
        
        # 分析标签名称中的层级分隔符
        hierarchy_patterns = []
        separators = ['/', '\\', '-', '_', '.', '|', ':', '>']
        
        for tag in tags:
            tag_name = tag.get('name', '')
            for sep in separators:
                if sep in tag_name:
                    hierarchy_patterns.append({
                        'tag': tag_name,
                        'separator': sep,
                        'levels': tag_name.split(sep),
                        'depth': len(tag_name.split(sep))
                    })
        
        if hierarchy_patterns:
            print(f"📊 发现 {len(hierarchy_patterns)} 个层级标签")
            
            # 分析分隔符使用情况
            sep_count = {}
            for pattern in hierarchy_patterns:
                sep = pattern['separator']
                sep_count[sep] = sep_count.get(sep, 0) + 1
            
            print(f"🔧 分隔符使用统计: {sep_count}")
            
            # 显示层级示例
            print(f"📋 层级标签示例:")
            for pattern in hierarchy_patterns[:10]:
                print(f"   '{pattern['tag']}' -> {pattern['levels']} (深度: {pattern['depth']})")
            
            # 分析最深层级
            max_depth = max(pattern['depth'] for pattern in hierarchy_patterns)
            print(f"📏 最大层级深度: {max_depth}")
            
            return hierarchy_patterns
        else:
            print("❌ 未发现明显的层级结构")
            return None
    
    def search_for_missing_tags(self, known_tags):
        """搜索可能遗漏的标签"""
        print("\n🔍 搜索可能遗漏的标签...")
        print("=" * 60)
        
        # 从备忘录中提取所有使用过的标签
        try:
            # 获取一些备忘录样本
            memo_params = self._generate_params({"limit": "100", "tz": "8:0"})
            headers = {"Authorization": self.token}
            
            response = requests.get(f"{self.base_url}/memo/updated/", 
                                  params=memo_params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    memos = data.get("data", [])
                    print(f"📝 获取到 {len(memos)} 条备忘录用于标签分析")
                    
                    # 提取所有标签
                    memo_tags = set()
                    for memo in memos:
                        tags = memo.get('tags', [])
                        memo_tags.update(tags)
                    
                    print(f"🏷️  从备忘录中发现 {len(memo_tags)} 个不同的标签")
                    
                    # 与已知标签对比
                    known_tag_names = {tag.get('name', '') for tag in known_tags}
                    missing_tags = memo_tags - known_tag_names
                    
                    if missing_tags:
                        print(f"❓ 可能遗漏的标签 ({len(missing_tags)} 个):")
                        for tag in list(missing_tags)[:20]:  # 显示前20个
                            print(f"   - {tag}")
                        
                        if len(missing_tags) > 20:
                            print(f"   ... 还有 {len(missing_tags) - 20} 个")
                    else:
                        print("✅ 没有发现遗漏的标签")
                    
                    return {
                        "memo_tags": list(memo_tags),
                        "missing_tags": list(missing_tags),
                        "comparison": {
                            "known_count": len(known_tag_names),
                            "memo_count": len(memo_tags),
                            "missing_count": len(missing_tags)
                        }
                    }
        
        except Exception as e:
            print(f"💥 搜索失败: {e}")
            return None

def main():
    # 配置token
    TOKEN = "Bearer 6782846|pguJkOHgJ21KYW4oHfrEF0syJvHRygKI5a53Mitf"
    
    tester = FlomoTagEnhancedTest(TOKEN)
    
    print("🚀 Flomo 标签 API 增强测试")
    print("=" * 60)
    
    # 1. 测试不同的标签端点
    print("\n1️⃣ 测试不同的标签端点")
    endpoint_results = tester.test_different_tag_endpoints()
    
    successful_endpoints = [ep for ep, result in endpoint_results.items() if result.get('success')]
    print(f"\n✅ 成功的端点: {successful_endpoints}")
    
    # 2. 深度测试分页
    print("\n2️⃣ 深度测试标签分页")
    all_tags = tester.test_tag_pagination_deeply()
    
    # 3. 分析标签层级结构
    print("\n3️⃣ 分析标签层级结构")
    hierarchy = tester.analyze_tag_hierarchy(all_tags)
    
    # 4. 搜索遗漏的标签
    print("\n4️⃣ 搜索可能遗漏的标签")
    missing_analysis = tester.search_for_missing_tags(all_tags)
    
    # 5. 综合分析报告
    print("\n" + "=" * 60)
    print("📊 综合分析报告")
    print("=" * 60)
    
    print(f"🎯 最终统计:")
    print(f"   通过标签API获取: {len(all_tags)} 个标签")
    if missing_analysis:
        print(f"   从备忘录发现: {missing_analysis['comparison']['memo_count']} 个标签")
        print(f"   可能遗漏: {missing_analysis['comparison']['missing_count']} 个标签")
    
    if hierarchy:
        print(f"   层级标签: {len(hierarchy)} 个")
    
    # 导出详细数据
    export_data = {
        "export_time": datetime.now().isoformat(),
        "endpoint_results": endpoint_results,
        "all_tags": all_tags,
        "hierarchy_analysis": hierarchy,
        "missing_analysis": missing_analysis
    }
    
    with open("flomo_tags_detailed.json", 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 详细数据已导出到 flomo_tags_detailed.json")
    print(f"\n🎉 增强测试完成！")

if __name__ == "__main__":
    main()