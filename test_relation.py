#!/usr/bin/env python3

import requests
import hashlib
import json
from datetime import datetime
from bs4 import BeautifulSoup
from html2text import html2text
import time

class FlomoCompleteAPI:
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
    
    def get_all_memos(self, limit_per_page=200):
        """获取所有备忘录"""
        all_memos = []
        latest_slug = None
        latest_updated_at = None
        page = 1
        
        while True:
            print(f"正在获取第 {page} 页数据...")
            
            search_params = {"limit": str(limit_per_page), "tz": "8:0"}
            
            # 添加分页参数
            if latest_slug and latest_updated_at:
                search_params.update({
                    "latest_slug": latest_slug,
                    "latest_updated_at": str(latest_updated_at)
                })
            
            params = self._generate_params(search_params)
            headers = {"Authorization": self.token}
            
            try:
                response = requests.get(f"{self.base_url}/memo/updated/", 
                                     params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 0:
                        memos = data.get("data", [])
                        
                        if not memos:
                            break
                        
                        all_memos.extend(memos)
                        print(f"第 {page} 页获取 {len(memos)} 条备忘录")
                        
                        # 如果这页结果少于限制数量，说明没有更多数据了
                        if len(memos) < limit_per_page:
                            break
                        
                        # 设置下一页参数
                        last_memo = memos[-1]
                        latest_slug = last_memo["slug"]
                        latest_updated_at = int(datetime.fromisoformat(last_memo["updated_at"]).timestamp())
                        
                        page += 1
                        # time.sleep(0.5)  # 避免请求过快
                    else:
                        print(f"API错误: {data.get('message')}")
                        break
                else:
                    print(f"HTTP错误: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"请求异常: {e}")
                break
        
        print(f"✅ 总共获取到 {len(all_memos)} 条备忘录")
        return all_memos
    
    def get_memo_recommendations(self, memo_slug, rec_type=1, no_same_tag=0):
        """
        获取备忘录的相关推荐
        
        Args:
            memo_slug: 备忘录的slug标识符
            rec_type: 推荐类型 (默认为1)
            no_same_tag: 是否排除相同标签 (0=不排除, 1=排除)
        """
        try:
            params = self._generate_params({
                "type": str(rec_type),
                "no_same_tag": str(no_same_tag)
            })
            
            headers = {"Authorization": self.token}
            url = f"{self.base_url}/memo/{memo_slug}/recommended"
            
            print(f"🔗 获取备忘录 {memo_slug} 的相关推荐...")
            
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    recommendations = data.get("data", [])
                    print(f"✅ 找到 {len(recommendations)} 条相关备忘录")
                    return recommendations
                else:
                    print(f"❌ API错误: {data.get('message')}")
                    return []
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"💥 获取推荐失败: {e}")
            return []
    
    def analyze_memo_relationships(self, memo_slug):
        """分析备忘录的关联关系"""
        recommendations = self.get_memo_recommendations(memo_slug)
        
        if not recommendations:
            return None
        
        # 分析相似度分布
        similarities = [float(rec["similarity"]) for rec in recommendations]
        
        # 分析标签分布
        all_tags = []
        for rec in recommendations:
            tags = rec["memo"].get("tags", [])
            all_tags.extend(tags)
        
        from collections import Counter
        tag_counter = Counter(all_tags)
        
        # 分析时间分布
        dates = []
        for rec in recommendations:
            created_at = rec["memo"].get("created_at")
            if created_at:
                dates.append(created_at[:7])  # YYYY-MM
        
        date_counter = Counter(dates)
        
        analysis = {
            "total_recommendations": len(recommendations),
            "similarity_stats": {
                "max": max(similarities),
                "min": min(similarities),
                "avg": sum(similarities) / len(similarities)
            },
            "top_tags": dict(tag_counter.most_common(10)),
            "date_distribution": dict(date_counter.most_common(12)),
            "high_similarity_count": len([s for s in similarities if s > 0.85]),
            "recommendations": recommendations
        }
        
        return analysis
    
    def find_memo_clusters(self, memos_sample=50):
        """
        发现备忘录的聚类关系
        
        Args:
            memos_sample: 要分析的备忘录样本数量
        """
        # 获取一些备忘录样本
        all_memos = self.get_all_memos()
        
        if len(all_memos) > memos_sample:
            # 取最新的N条备忘录作为样本
            sample_memos = all_memos[:memos_sample]
        else:
            sample_memos = all_memos
        
        print(f"🔍 分析 {len(sample_memos)} 条备忘录的聚类关系...")
        
        clusters = {}
        
        for i, memo in enumerate(sample_memos):
            memo_slug = memo.get("slug")
            print(f"分析备忘录 {i+1}/{len(sample_memos)}: {memo_slug}")
            
            # 获取推荐
            analysis = self.analyze_memo_relationships(memo_slug)
            
            if analysis:
                # 找出高相似度的备忘录
                high_sim_memos = []
                for rec in analysis["recommendations"]:
                    if float(rec["similarity"]) > 0.85:  # 高相似度阈值
                        high_sim_memos.append({
                            "slug": rec["memo"]["slug"],
                            "similarity": rec["similarity"],
                            "tags": rec["memo"].get("tags", [])
                        })
                
                if high_sim_memos:
                    clusters[memo_slug] = {
                        "memo_info": {
                            "slug": memo_slug,
                            "content_preview": memo.get("content", "")[:100],
                            "tags": memo.get("tags", []),
                            "created_at": memo.get("created_at")
                        },
                        "related_memos": high_sim_memos,
                        "analysis": analysis
                    }
            
            # 避免请求过快
            if i < len(sample_memos) - 1:
                time.sleep(1)
        
        print(f"✅ 发现 {len(clusters)} 个备忘录聚类")
        return clusters
    
    def export_relationship_network(self, clusters, filename="flomo_network.json"):
        """导出备忘录关系网络"""
        network_data = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "total_clusters": len(clusters),
                "total_nodes": 0,
                "total_edges": 0
            }
        }
        
        # 收集所有节点
        all_slugs = set()
        
        for main_slug, cluster_data in clusters.items():
            all_slugs.add(main_slug)
            for related in cluster_data["related_memos"]:
                all_slugs.add(related["slug"])
        
        # 创建节点
        for slug in all_slugs:
            node = {"id": slug, "type": "memo"}
            
            # 如果是主节点，添加更多信息
            if slug in clusters:
                cluster_data = clusters[slug]
                node.update({
                    "content_preview": cluster_data["memo_info"]["content_preview"],
                    "tags": cluster_data["memo_info"]["tags"],
                    "created_at": cluster_data["memo_info"]["created_at"],
                    "is_main_node": True
                })
            else:
                node["is_main_node"] = False
            
            network_data["nodes"].append(node)
        
        # 创建边
        for main_slug, cluster_data in clusters.items():
            for related in cluster_data["related_memos"]:
                edge = {
                    "source": main_slug,
                    "target": related["slug"],
                    "similarity": float(related["similarity"]),
                    "type": "similarity"
                }
                network_data["edges"].append(edge)
        
        # 更新元数据
        network_data["metadata"]["total_nodes"] = len(network_data["nodes"])
        network_data["metadata"]["total_edges"] = len(network_data["edges"])
        
        # 导出到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 关系网络已导出到 {filename}")
        return network_data

def main():
    # 配置token
    TOKEN = "Bearer 6782846|pguJkOHgJ21KYW4oHfrEF0syJvHRygKI5a53Mitf"
    
    api = FlomoCompleteAPI(TOKEN)
    
    print("🚀 Flomo 完整 API 客户端演示")
    print("="*60)
    
    # 1. 测试获取单个备忘录的推荐
    print("\n1️⃣ 测试备忘录推荐功能")
    test_slug = "MTUyNzU0MDU3"  # 使用你提供的示例slug
    analysis = api.analyze_memo_relationships(test_slug)
    
    if analysis:
        print(f"📊 推荐分析结果:")
        print(f"   总推荐数: {analysis['total_recommendations']}")
        print(f"   相似度范围: {analysis['similarity_stats']['min']:.3f} - {analysis['similarity_stats']['max']:.3f}")
        print(f"   平均相似度: {analysis['similarity_stats']['avg']:.3f}")
        print(f"   高相似度(>0.85): {analysis['high_similarity_count']} 条")
        print(f"   热门标签: {list(analysis['top_tags'].keys())[:5]}")
    
    # 2. 发现备忘录聚类
    print(f"\n2️⃣ 备忘录聚类分析")
    clusters = api.find_memo_clusters(memos_sample=10)  # 小样本测试
    
    if clusters:
        print(f"📈 聚类分析结果:")
        for slug, cluster in list(clusters.items())[:3]:  # 显示前3个聚类
            print(f"\n   聚类中心: {slug}")
            print(f"   内容预览: {cluster['memo_info']['content_preview']}...")
            print(f"   相关备忘录: {len(cluster['related_memos'])} 条")
            print(f"   标签: {cluster['memo_info']['tags']}")
    
    # 3. 导出关系网络
    print(f"\n3️⃣ 导出关系网络")
    if clusters:
        network = api.export_relationship_network(clusters)
        print(f"🌐 网络统计:")
        print(f"   节点数: {network['metadata']['total_nodes']}")
        print(f"   边数: {network['metadata']['total_edges']}")
    
    print(f"\n🎉 演示完成！")

if __name__ == "__main__":
    main()