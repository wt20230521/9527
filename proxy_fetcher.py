#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理抓取与验证工具 - GitHub Actions 自动运行版
无交互，直接抓取所有国家并输出
"""

import requests
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
import socket
from collections import Counter


@dataclass
class Proxy:
    """代理对象"""
    ip: str
    port: int
    protocol: str = "http"
    country_code: str = ""
    country_name: str = ""
    source: str = ""
    latency: float = -1.0
    is_valid: bool = False
    is_anonymous: bool = False
    is_home_broadband: bool = False
    real_ip: str = ""
    node_name: str = ""

    def __str__(self):
        return f"{self.ip}:{self.port}"

    def to_node_format(self) -> str:
        """输出为节点格式: IP:端口#地区 或 IP:端口#地区家宽"""
        if self.is_home_broadband:
            return f"{self.ip}:{self.port}#{self.country_name}家宽"
        else:
            return f"{self.ip}:{self.port}#{self.country_name}"


class ProxyFetcher:
    """代理抓取器"""

    COUNTRY_MAP = {
        'TW': '台湾', 'HK': '香港', 'SG': '新加坡', 'JP': '日本',
        'US': '美国', 'KR': '韩国'
    }

    CF_COUNTRIES = {
        'TW': 'https://cf.776771.xyz/TW',
        'HK': 'https://cf.776771.xyz/HK',
        'SG': 'https://cf.776771.xyz/SG',
        'JP': 'https://cf.776771.xyz/JP',
        'US': 'https://cf.776771.xyz/US',
        'KR': 'https://cf.776771.xyz/KR',
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def fetch_from_cf_country(self, country_code: str) -> List[Proxy]:
        """从 cf.776771.xyz 抓取指定国家的代理"""
        proxies = []
        url = self.CF_COUNTRIES.get(country_code)
        if not url:
            return []

        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()

            pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):([\d]+)(?:#(.+))?')

            for match in pattern.finditer(resp.text):
                ip, port, remark = match.groups()
                remark = remark.strip() if remark else ""

                if self._is_valid_ip(ip):
                    is_home = "家宽" in remark or "疑似家宽" in remark

                    proxy = Proxy(
                        ip=ip,
                        port=int(port),
                        protocol="http",
                        country_code=country_code,
                        country_name=self.COUNTRY_MAP.get(country_code, country_code),
                        source=f"cf.776771.xyz/{country_code}",
                        is_home_broadband=is_home,
                        node_name=remark if remark else f"{self.COUNTRY_MAP.get(country_code, country_code)}节点"
                    )
                    proxies.append(proxy)

            print(f"[✓] cf.776771.xyz/{country_code}({self.COUNTRY_MAP.get(country_code, '')}): {len(proxies)} 个")
            return proxies

        except Exception as e:
            print(f"[✗] cf.776771.xyz/{country_code}: {e}")
            return []

    def fetch_all(self) -> List[Proxy]:
        """抓取所有国家代理"""
        all_proxies = []

        print("📥 抓取 cf.776771.xyz 各国代理...")
        for cc in self.CF_COUNTRIES.keys():
            proxies = self.fetch_from_cf_country(cc)
            all_proxies.extend(proxies)
            time.sleep(0.3)

        unique = self._deduplicate(all_proxies)
        print(f"\n[📊] 去重后共 {len(unique)} 个唯一代理")

        country_count = Counter(p.country_code for p in unique)
        print("📍 各国分布:")
        for cc, count in country_count.most_common():
            name = self.COUNTRY_MAP.get(cc, cc)
            print(f"  {cc}({name}): {count} 个")

        return unique

    def _is_valid_ip(self, ip: str) -> bool:
        try:
            socket.inet_aton(ip)
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
        except:
            return False

    def _deduplicate(self, proxies: List[Proxy]) -> List[Proxy]:
        seen = set()
        unique = []
        for p in proxies:
            key = f"{p.protocol}://{p.ip}:{p.port}"
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique


class ProxyValidator:
    """代理验证器"""

    TEST_URLS = {
        'http': ["http://httpbin.org/get", "http://icanhazip.com"],
        'https': ["https://httpbin.org/get", "https://icanhazip.com"]
    }
    TIMEOUT = 15

    def __init__(self, max_workers: int = 50):
        self.max_workers = max_workers
        self.local_ip = self._get_local_ip()
        print(f"[ℹ] 本机IP: {self.local_ip}")

    def _get_local_ip(self) -> str:
        try:
            resp = requests.get("https://icanhazip.com", timeout=10)
            return resp.text.strip()
        except:
            return ""

    def validate_single(self, proxy: Proxy) -> Proxy:
        test_urls = self.TEST_URLS.get(proxy.protocol, self.TEST_URLS['http'])
        test_url = test_urls[0]

        proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
        proxies = {"http": proxy_url, "https": proxy_url}

        start_time = time.time()
        try:
            resp = requests.get(
                test_url, 
                proxies=proxies, 
                timeout=self.TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            latency = time.time() - start_time

            proxy.latency = round(latency, 2)
            proxy.is_valid = True

            try:
                data = resp.json() if 'json' in resp.headers.get('Content-Type', '') else {}
                origin = data.get('origin', '')
                proxy.real_ip = origin
                if self.local_ip and self.local_ip not in origin:
                    proxy.is_anonymous = True
            except:
                proxy.real_ip = resp.text.strip()[:50]

        except Exception:
            proxy.is_valid = False

        return proxy

    def validate_all(self, proxies: List[Proxy]) -> Tuple[List[Proxy], List[Proxy]]:
        valid_proxies = []
        invalid_proxies = []

        print(f"\n[🔍] 开始验证 {len(proxies)} 个代理...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.validate_single, proxy): proxy 
                for proxy in proxies
            }

            completed = 0
            for future in as_completed(future_to_proxy):
                completed += 1
                proxy = future.result()

                if proxy.is_valid:
                    valid_proxies.append(proxy)
                else:
                    invalid_proxies.append(proxy)

                if completed % 50 == 0 or completed == len(proxies):
                    print(f"  进度: {completed}/{len(proxies)} | 有效: {len(valid_proxies)} | 无效: {len(invalid_proxies)}")

        valid_proxies.sort(key=lambda p: p.latency)

        print(f"\n[✅] 验证完成: 有效 {len(valid_proxies)} 个, 无效 {len(invalid_proxies)} 个")
        return valid_proxies, invalid_proxies


def main():
    print("=" * 70)
    print("🚀 代理抓取与验证工具 - GitHub Actions 版")
    print("=" * 70)

    # 1. 抓取
    print("\n📥 抓取代理...")
    fetcher = ProxyFetcher()
    all_proxies = fetcher.fetch_all()

    if not all_proxies:
        print("[!] 未抓取到任何代理")
        return

    # 2. 验证
    print("\n" + "=" * 70)
    validator = ProxyValidator(max_workers=100)
    valid_proxies, invalid_proxies = validator.validate_all(all_proxies)

    # 3. 统计
    print("\n" + "=" * 70)
    print("📊 验证结果统计")
    print("=" * 70)
    print(f"总代理数: {len(all_proxies)}")
    print(f"有效代理: {len(valid_proxies)} ({len(valid_proxies)/len(all_proxies)*100:.1f}%)")
    print(f"无效代理: {len(invalid_proxies)}")

    country_valid = Counter(p.country_code for p in valid_proxies)
    print("\n📍 各国有效代理分布:")
    for cc, count in country_valid.most_common():
        name = fetcher.COUNTRY_MAP.get(cc, cc)
        print(f"  {cc}({name}): {count} 个")

    if valid_proxies:
        avg_latency = sum(p.latency for p in valid_proxies) / len(valid_proxies)
        print(f"\n⚡ 平均延迟: {avg_latency:.2f}s")
        print(f"🏆 最快代理: {valid_proxies[0]} ({valid_proxies[0].latency}s)")

    # 4. 导出节点格式
    print("\n💾 导出节点格式...")
    with open("proxies_valid_node.txt", "w", encoding="utf-8") as f:
        for p in valid_proxies:
            f.write(p.to_node_format() + "\n")
    print(f"[✅] 已保存: proxies_valid_node.txt ({len(valid_proxies)} 条)")

    # 5. 导出按国家分类
    print("\n📁 按国家导出...")
    from collections import defaultdict
    country_groups = defaultdict(list)
    for p in valid_proxies:
        cc = p.country_code if p.country_code else "UNKNOWN"
        country_groups[cc].append(p)

    for cc, group in sorted(country_groups.items()):
        filename = f"proxies_{cc}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for p in group:
                f.write(p.to_node_format() + "\n")
        print(f"  {cc}: {len(group)} 个 → {filename}")

    print("\n✨ 完成!")


if __name__ == "__main__":
    main()
