import json
from playwright.sync_api import sync_playwright

def crawl_idolmaster_schedule():
    extracted_data = []
    
    # 1. 사용자가 원하는 카테고리 키워드 세팅 (라디오, 굿즈, 콜라보/캠페인, 배신방송)
    valid_keywords = [
        "ラジオ", "라디오", "radio", 
        "グッズ", "굿즈", "goods", 
        "コラボ", "콜라보", "キャンペーン", "캠페인", 
        "配信番組", "配信", "배신"
    ]

    # 2. SVG Path 지문(Signature)과 브랜드 매핑 딕셔너리
    brand_signatures = {
        "M31.54,14.47c1": "본가(765PRO)",
        "M18.55,19.49c.16": "데레(CG)",
        "M28.27,13.16c2.07": "밀리(ML)",
        "M25.96,9.67c1.06": "샤니(SC)",
        "M35.52,9.47c": "사이(SideM)",
        "M20.65,4.57c0-": "가쿠(학원마스)",
        "m24.54,24.81c-": "876(DS)"
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("페이지에 접속 중입니다...")
        page.goto("https://idolmaster-official.jp/schedule")

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        print("숨겨진 스케줄을 불러오기 위해 화면을 아래로 스크롤합니다...")
        last_height = page.evaluate("document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 15 

        while scroll_count < max_scrolls:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                print("더 이상 불러올 데이터가 없습니다. 스크롤 완료!")
                break
                
            last_height = new_height
            scroll_count += 1
            print(f"{scroll_count}번째 스크롤 완료, 데이터 로딩 중...")

        print("데이터 추출을 시작합니다...")
        
        # 내부 함수: 각 스케줄 아이템에서 데이터를 뽑아내는 로직 (중복 코드 제거)
        def extract_item_data(item, base_date):
            # 카테고리 추출
            category_elems = item.locator('li[class*="style_category"]').all_inner_texts()
            category_text = ", ".join(category_elems)

            # 타겟 카테고리인지 확인
            is_target = any(keyword.lower() in category_text.lower() for keyword in valid_keywords)

            if is_target:
                # 제목 & 링크
                link_elem = item.locator('a[class*="style_title_link"]')
                title = link_elem.inner_text().strip() if link_elem.count() > 0 else "제목 없음"
                
                href = link_elem.get_attribute("href") if link_elem.count() > 0 else ""
                link = f"https://idolmaster-official.jp{href}" if href and href.startswith("/") else href

                # 날짜 & 시간
                time_elem = item.locator('p[class*="style_head_dsdate"]')
                time_text = time_elem.inner_text().strip() if time_elem.count() > 0 else ""
                final_date = f"{base_date} {time_text}".strip() if base_date != "진행 중(実施中)" else f"{base_date} ({time_text})".strip()

                # === 🌟 초고급 기술: SVG Path로 브랜드 식별하기 ===
                brands = set() # 중복 제거를 위해 set 사용 (한 이벤트에 데레+밀리 같이 나올 수도 있음)
                svg_paths = item.locator('.style_brand_item__tpY75 svg path').all()
                
                for path_elem in svg_paths:
                    d_attr = path_elem.get_attribute("d")
                    if d_attr:
                        # 우리가 정의한 지문으로 시작하는지 확인
                        for signature, brand_name in brand_signatures.items():
                            if d_attr.startswith(signature):
                                brands.add(brand_name)
                
                # 브랜드가 하나도 매칭 안 되면 공통/기타 처리
                brand_text = ", ".join(list(brands)) if brands else "기타/전체"

                # 결과 저장
                extracted_data.append({
                    "brand": brand_text,    # 👈 브랜드 정보 추가!
                    "title": title,
                    "date": final_date,
                    "category": category_text,
                    "link": link
                })

        # ---------------------------------------------------------
        # 1. '진행 중(Ongoing)' 장기 스케줄
        # ---------------------------------------------------------
        ongoing_groups = page.locator('li[data-type="ongoing"]').all()
        for group in ongoing_groups:
            # 장기 스케줄 내부 아이템 탐색
            schedule_items = group.locator('div[class*="style_article"]').all()
            for item in schedule_items:
                extract_item_data(item, "진행 중(実施中)")

        # ---------------------------------------------------------
        # 2. '특정 날짜' 일반 스케줄
        # ---------------------------------------------------------
        day_groups = page.locator('li[id^="schedule_list_"]').all()
        for group in day_groups:
            group_id = group.get_attribute("id")
            base_date = group_id.replace("schedule_list_", "") if group_id else "날짜 모름"

            schedule_items = group.locator('li[class*="style_day_item"]').all()
            for item in schedule_items:
                extract_item_data(item, base_date)

        browser.close()

    # 추출한 데이터를 JSON 파일로 저장
    with open("schedule_data.json", "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    print(f"크롤링 완료! 총 {len(extracted_data)}개의 항목을 'schedule_data.json'에 저장했습니다.")

if __name__ == "__main__":
    crawl_idolmaster_schedule()