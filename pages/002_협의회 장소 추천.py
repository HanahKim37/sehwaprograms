import streamlit as st
import folium
from folium import Icon
from geopy.geocoders import OpenCage
from streamlit_folium import st_folium
import uuid

# 페이지 설정
st.set_page_config(page_title="협의회 추천 장소", layout="wide")

# 제목
st.title("📍 협의회 추천 장소")
st.write("장소 이름을 입력하면 지도에 자동으로 표시됩니다.")

# 세션 상태 초기화
if "places" not in st.session_state:
    st.session_state.places = []

if "selected_place_id" not in st.session_state:
    st.session_state.selected_place_id = None

# ✅ OpenCage 지오코딩 함수
def geocode_address(address):
    geolocator = OpenCage(api_key="aafcf540160d4faba8c2a5e64f296acc")
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            st.warning(f"'{address}'에 대한 위치를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"지오코딩 에러: {e}")
    return None, None

# 마커 색상 결정
def get_marker_color(capacity):
    return {
        "5명 이하": "green",
        "5~10명": "blue",
        "10~20명": "orange",
        "20명 이상": "red"
    }.get(capacity, "gray")

# 입력 폼
with st.form("place_form", clear_on_submit=True):
    st.subheader("📝 장소 입력")
    place = st.text_input("장소 이름", value="")
    capacity = st.selectbox("적정 인원", ["5명 이하", "5~10명", "10~20명", "20명 이상"])
    department = st.text_input("교과/부서")
    recommender = st.text_input("추천인")
    note = st.text_area("비고")
    submitted = st.form_submit_button("지도에 추가하기")

# 장소 추가 처리
if submitted and place:
    lat, lon = geocode_address(place)
    if lat and lon:
        st.session_state.places.append({
            "id": str(uuid.uuid4()),
            "place": place,
            "lat": lat,
            "lon": lon,
            "capacity": capacity,
            "department": department,
            "recommender": recommender,
            "note": note,
        })
    else:
        st.error(f"장소 '{place}'를 찾을 수 없습니다.")

# 지도 생성
default_location = [37.5665, 126.9780]
map_center = default_location

# 선택된 장소가 있다면 확대
zoom_level = 6
if st.session_state.selected_place_id:
    for entry in st.session_state.places:
        if entry["id"] == st.session_state.selected_place_id:
            map_center = [entry["lat"], entry["lon"]]
            zoom_level = 15
            break

m = folium.Map(location=map_center, zoom_start=zoom_level)

# 마커 추가
for entry in st.session_state.places:
    color = get_marker_color(entry["capacity"])
    popup_text = f"""<b>{entry['place']}</b><br>
    적정 인원: {entry['capacity']}<br>
    교과/부서: {entry['department']}<br>
    추천인: {entry['recommender']}<br>
    비고: {entry['note']}"""
    
    folium.Marker(
        [entry["lat"], entry["lon"]],
        tooltip=entry["place"],
        popup=folium.Popup(popup_text, max_width=300),
        icon=Icon(color=color)
    ).add_to(m)

# 레이아웃: 지도와 리스트 나란히
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ 추천 장소 지도")
    st_folium(m, width=800, height=600)

with col2:
    st.subheader("📋 저장된 장소 리스트")
    grouped = {}
    for entry in st.session_state.places:
        grouped.setdefault(entry["capacity"], []).append(entry)

    for capacity, entries in grouped.items():
        with st.expander(f"👥 {capacity} ({len(entries)}개)", expanded=True):
            for e in entries:
                if st.button(f"📍 {e['place']}", key=f"select_{e['id']}"):
                    st.session_state.selected_place_id = e["id"]

                # 삭제 버튼과 비밀번호
                delete_col1, delete_col2 = st.columns([1, 2])
                with delete_col1:
                    show_pw = st.button("❌ 삭제", key=f"show_delete_{e['id']}")
                with delete_col2:
                    if f"delete_{e['id']}_pw" not in st.session_state:
                        st.session_state[f"delete_{e['id']}_pw"] = ""

                    if show_pw:
                        st.session_state[f"delete_{e['id']}_pw"] = st.text_input(
                            "비밀번호 입력", type="password", key=f"pw_input_{e['id']}"
                        )

                    if st.session_state.get(f"delete_{e['id']}_pw") == "haeunkim":
                        st.session_state.places = [p for p in st.session_state.places if p["id"] != e["id"]]
                        st.success(f"'{e['place']}'가 삭제되었습니다.")
                        st.experimental_rerun()
