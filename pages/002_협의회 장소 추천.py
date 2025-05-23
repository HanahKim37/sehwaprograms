import streamlit as st
import folium
from folium import Icon
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import time

st.set_page_config(page_title="협의회 추천 장소", layout="wide")
st.title("📍 협의회 추천 장소")
st.write("장소 이름을 입력하면 지도에 자동으로 표시됩니다.")

# 장소 입력 폼
with st.form("place_form", clear_on_submit=True):
    st.subheader("📝 장소 입력")
    place = st.text_input("장소 이름", value="")
    capacity = st.selectbox("적정 인원", ["5명 이하", "5~10명", "10~20명", "20명 이상"])
    department = st.text_input("교과/부서")
    recommender = st.text_input("추천인")
    note = st.text_area("비고")
    submitted = st.form_submit_button("지도에 추가하기")

# 세션 상태 초기화
if "places" not in st.session_state:
    st.session_state.places = []

# id 없는 항목에 id 추가
for p in st.session_state.places:
    if "id" not in p:
        p["id"] = f"{p['place']}_{time.time()}"

if "delete_target_id" not in st.session_state:
    st.session_state.delete_target_id = None

# 지도에서 확대 표시할 위치
if "focused_location" not in st.session_state:
    st.session_state.focused_location = None

# 지오코딩
def geocode_address(address):
    geolocator = Nominatim(user_agent="my_unique_streamlit_app_sehwa_2025")
    time.sleep(1)
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

# 장소 추가
if submitted and place:
    lat, lon = geocode_address(place)
    if lat and lon:
        st.session_state.places.append({
            "id": f"{place}_{time.time()}",
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

# 마커 색상
def get_marker_color(capacity):
    return {
        "5명 이하": "green",
        "5~10명": "blue",
        "10~20명": "orange",
        "20명 이상": "red"
    }.get(capacity, "gray")

# 지도 중심 위치
if st.session_state.focused_location:
    map_center = st.session_state.focused_location
    zoom_level = 15
else:
    map_center = [37.5665, 126.9780]
    zoom_level = 6

# 지도 생성
m = folium.Map(location=map_center, zoom_start=zoom_level)
for entry in st.session_state.places:
    popup_text = f"""<b>{entry['place']}</b><br>
    적정 인원: {entry['capacity']}<br>
    교과/부서: {entry['department']}<br>
    추천인: {entry['recommender']}<br>
    비고: {entry['note']}"""
    folium.Marker(
        [entry["lat"], entry["lon"]],
        tooltip=entry["place"],
        popup=folium.Popup(popup_text, max_width=300),
        icon=Icon(color=get_marker_color(entry["capacity"]))
    ).add_to(m)

# 컬럼 나누기
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ 추천 장소 지도")
    st_folium(m, width=800, height=600)

with col2:
    st.subheader("📋 장소 목록 (적정 인원별)")

    grouped = {}
    for entry in st.session_state.places:
        grouped.setdefault(entry["capacity"], []).append(entry)

    for capacity_group in ["5명 이하", "5~10명", "10~20명", "20명 이상"]:
        entries = grouped.get(capacity_group, [])
        if entries:
            with st.expander(f"{capacity_group} ({len(entries)}곳)", expanded=True):
                for e in entries:
                    col_entry, col_delete = st.columns([4, 1])
                    with col_entry:
                        if st.button(f"📌 {e['place']}", key=f"focus_{e['id']}"):
                            st.session_state.focused_location = [e["lat"], e["lon"]]
                            st.rerun()

                        st.markdown(f"""
                        - 교과/부서: {e['department']}
                        - 추천인: {e['recommender']}
                        """)

                    with col_delete:
                        if st.button("❌", key=f"delete_btn_{e['id']}"):
                            st.session_state.delete_target_id = e["id"]
                            st.rerun()

                    if st.session_state.delete_target_id == e["id"]:
                        pw = st.text_input("비밀번호 입력", type="password", key=f"pw_{e['id']}")
                        if st.button("삭제 확인", key=f"confirm_delete_{e['id']}"):
                            if pw == "haeunkim":
                                st.session_state.places = [p for p in st.session_state.places if p["id"] != e["id"]]
                                st.session_state.delete_target_id = None
                                st.session_state.focused_location = None
                                st.success(f"'{e['place']}' 삭제 완료")
                                st.rerun()
                            else:
                                st.error("❗ 비밀번호가 틀렸습니다.")
