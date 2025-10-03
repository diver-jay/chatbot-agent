# import os
# import glob
# import random
# import streamlit as st


# # 키워드 매칭 함수
# def match_keywords_to_category(response_text):
#     """응답 텍스트를 분석하여 가장 적합한 카테고리를 반환"""
#
#     # 확장된 키워드 매핑 (우선순위별로 정렬)
#     keyword_categories = {
#         'emotions': {
#             'keywords': ['기쁘', '행복', '즐거', '웃', '좋아', '사랑', '고마워', '감사', '최고', '완전', '대박', '짱',
#                         '슬프', '우울', '힘들', '아쉬', '속상', '걱정', '불안', '화나', '짜증', '놀라', '깜짝', '무서'],
#             'weight': 1
#         },
#         'food': {
#             'keywords': ['음식', '밥', '라면', '피자', '치킨', '커피', '디저트', '과일', '야식', '맛있', '먹', '배고',
#                         '요리', '마시', '달콤', '시원', '따뜻', '간식', '점심', '저녁', '아침'],
#             'weight': 2
#         },
#         'animals': {
#             'keywords': ['강아지', '고양이', '동물', '귀여운', '귀여', '펫', '새', '물고기', '토끼', '햄스터', '멍멍', '야옹'],
#             'weight': 2
#         },
#         'activities': {
#             'keywords': ['운동', '공부', '게임', '영화', '음악', '독서', '책', '여행', '쇼핑', '요리', '청소',
#                         '일', '회사', '학교', '숙제', '시험', '취미', '산책'],
#             'weight': 1.5
#         },
#         'weather': {
#             'keywords': ['날씨', '비', '눈', '바람', '더위', '추위', '맑', '흐림', '구름', '햇살', '따뜻', '시원',
#                         '덥', '춥', '바람', '폭우', '눈사람'],
#             'weight': 2
#         },
#         'general': {
#             'keywords': ['안녕', '좋은', '일상', '하루', '생활', '친구', '사람', '오늘', '내일', '어제', '시간'],
#             'weight': 0.5
#         }
#     }
#
#     # 응답 텍스트에서 키워드 찾기 (가중치 적용)
#     category_scores = {}
#
#     for category, data in keyword_categories.items():
#         keywords = data['keywords']
#         weight = data['weight']
#         matches = sum(1 for keyword in keywords if keyword in response_text)
#         category_scores[category] = matches * weight
#
#     # 가장 높은 점수의 카테고리 선택
#     if category_scores and max(category_scores.values()) > 0:
#         selected_category = max(category_scores.items(), key=lambda x: x[1])[0]
#     else:
#         selected_category = 'general'  # 기본값
#
#     # 디버깅을 위한 출력 (개발 시에만)
#     print(f"Response text: {response_text[:50]}...")
#     print(f"Category scores: {category_scores}")
#     print(f"Selected category: {selected_category}")
#
#     return selected_category
#
#
# # 이미지 선택 함수
# def select_image_for_context(response_text):
#     """AI 응답 내용을 분석하여 적절한 이미지를 선택"""
#
#     # 이미지 디렉토리 확인
#     images_dir = "images"
#     if not os.path.exists(images_dir):
#         return None
#
#     # 키워드 매칭으로 카테고리 선택
#     selected_category = match_keywords_to_category(response_text)
#
#     # 선택된 카테고리에서 이미지 선택
#     category_path = os.path.join(images_dir, selected_category)
#     if os.path.exists(category_path):
#         # 모든 이미지 형식 지원
#         image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.JPG', '*.JPEG', '*.PNG', '*.GIF']
#         image_files = []
#         for ext in image_extensions:
#             image_files.extend(glob.glob(os.path.join(category_path, ext)))
#
#         if image_files:
#             # 세션 상태를 이용해 최근 사용한 이미지 추적 (다양성 증가)
#             if 'recent_images' not in st.session_state:
#                 st.session_state.recent_images = []
#
#             # 최근 사용한 이미지 제외하고 선택
#             available_images = [img for img in image_files if img not in st.session_state.recent_images[-2:]]
#             if not available_images:
#                 available_images = image_files  # 모든 이미지가 최근 사용됐다면 전체에서 선택
#
#             selected_image = random.choice(available_images)
#
#             # 최근 사용한 이미지 목록 업데이트
#             st.session_state.recent_images.append(selected_image)
#             if len(st.session_state.recent_images) > 5:  # 최근 5개만 기억
#                 st.session_state.recent_images.pop(0)
#
#             print(f"Selected image: {selected_image}")
#             return selected_image
#
#     return None
