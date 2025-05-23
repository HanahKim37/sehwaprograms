import streamlit as st
import folium
from folium import Icon
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

st.set_page_config(page_title="협의회 추천 장소", layout="wide")

st.title("📍 협의회 추천 장소")
st.write("장소 이름을 입력하면 지도에 자동으로 표시됩니다.")

# 장소 정보 입력
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

# 지오코딩 함수
def geocode_address(address):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

# 장소 추가
if submitted and place:
    lat, lon = geocode_address(place)
    if lat and lon:
        st.session_state.places.append({
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

# 인원 수에 따른 마커 색상 지정
def get_marker_color(capacity):
    if capacity == "5명 이하":
        return "green"
    elif capacity == "5~10명":
        return "blue"
    elif capacity == "10~20명":
        return "orange"
    else:
        return "red"

# 지도 그리기
m = folium.Map(location=[37.5665, 126.9780], zoom_start=6)
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

# 지도 출력
st.subheader("🗺️ 추천 장소 지도")
st_folium(m, width=800, height=600)
