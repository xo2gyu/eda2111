import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Population trends 데이터셋**  
                - 설명: 설명: 대한민국의 연도별 지역별 인구통계를 기록한 데이터로, 전국 및 각 시·도의 인구 수, 출생아 수, 사망자 수 등이 포함되어 있으며, 인구 구조 및 변화 추이를 분석하는 데 활용됨.
                - 주요 변수:  
                  - `연도`: 해당 통계가 기록된 연도 
                  - `지역`: 전국 또는 각 시·도의 명칭 (예: 서울, 경기, 전북 등) 
                  - `인구`: 해당 지역의 총 인구 수
                  - `출생아수(명)`: 해당 지역에서 해당 연도에 출생한 신생아 수  
                  - `사망자수(명)`: 해당 지역에서 해당 연도에 사망한 인원 수 
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 population_trends EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded_file)

        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화",
        ])

        # 1. 기초통계
        with tabs[0]:
            df = pd.read_csv(uploaded_file)
	    df_sejong = df[df['지역'] == '세종'].copy()
	    df_sejong = df_sejong.replace('-', 0)

	    cols_to_numeric = ['인구', '출생아수(명)', '사망자수(명)']
	    for col in cols_to_numeric:
   	        df_sejong[col] = pd.to_numeric(df_sejong[col], errors='coerce').fillna(0)

	    st.subheader("전처리된 세종 데이터 미리보기")
	    st.dataframe(df_sejong)

	    st.subheader("요약 통계 (describe)")
	    st.dataframe(df_sejong.describe())

	    st.subheader("데이터프레임 구조 (info)")
	    from io import StringIO

	    buffer = StringIO()
	    df_sejong.info(buf=buffer)
	    info_str = buffer.getvalue()
	    st.text(info_str)


        # 2. 연도별 추이
        with tabs[1]:
            df = df.replace('-', 0)

            cols_to_numeric = ['인구', '출생아수(명)', '사망자수(명)']
            for col in cols_to_numeric:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            df_nat = df[df['지역'] == '전국'].copy()
            df_nat = df_nat.sort_values('연도')

            import matplotlib.pyplot as plt

            fig, ax = plt.subplots()
            ax.plot(df_nat['연도'], df_nat['인구'], marker='o', label='Population')

            recent = df_nat.tail(3)
            avg_births = recent['출생아수(명)'].mean()
            avg_deaths = recent['사망자수(명)'].mean()
            net_change_per_year = avg_births - avg_deaths

            last_year = df_nat['연도'].max()
            last_pop = df_nat.loc[df_nat['연도'] == last_year, '인구'].values[0]

            years_to_predict = 2035 - last_year
            pred_pop = last_pop + net_change_per_year * years_to_predict

            ax.plot(2035, pred_pop, 'ro', label='2035 prediction')
            ax.set_title("Population trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()

            st.pyplot(fig)

        # 3. 지역별 분석
        with tabs[2]:
            df = df.replace('-', 0)

            cols_to_numeric = ['인구']
            for col in cols_to_numeric:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            df = df[df['지역'] != '전국']

            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            df['Region_Eng'] = df['지역'].map(region_map)

            recent_years = sorted(df['연도'].unique())[-5:]
            df_recent = df[df['연도'].isin(recent_years)]

            pop_change = (
                df_recent.groupby('Region_Eng')['인구']
                .agg(['first', 'last'])
                .reset_index()
            )
            pop_change['Change'] = (pop_change['last'] - pop_change['first']) / 1000
            pop_change['Rate'] = ((pop_change['last'] - pop_change['first']) / pop_change['first']) * 100

            pop_change_sorted = pop_change.sort_values('Change', ascending=False)

            sns.set_style("whitegrid")
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.barplot(data=pop_change_sorted, x='Change', y='Region_Eng', ax=ax1, palette='Blues_d')
            for i, v in enumerate(pop_change_sorted['Change']):
                ax1.text(v if v >= 0 else v - 10, i, f"{v:.1f}", color='black', va='center')
            ax1.set_title("Population Change (last 5 years)")
            ax1.set_xlabel("Change (thousand people)")
            ax1.set_ylabel("Region")

            st.pyplot(fig1)

            pop_change_sorted_rate = pop_change.sort_values('Rate', ascending=False)

            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(data=pop_change_sorted_rate, x='Rate', y='Region_Eng', ax=ax2, palette='Greens_d')
            for i, v in enumerate(pop_change_sorted_rate['Rate']):
                ax2.text(v if v >= 0 else v - 1, i, f"{v:.1f}%", color='black', va='center')
            ax2.set_title("Population Change Rate (last 5 years)")
            ax2.set_xlabel("Change rate (%)")
            ax2.set_ylabel("Region")

            st.pyplot(fig2)

            st.markdown("""
            **Interpretation:**  
            The first chart shows the absolute population change (in thousands) over the last 5 years by region.  
            The second chart shows the percentage change over the same period.  
            Regions with positive values are growing, while negative values indicate population decline.  
            Compare the two charts to see where population growth is strongest both in absolute and relative terms.
            """)

        # 4. 변화량 분석
        with tabs[3]:
            df = df.replace('-', 0)

            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
            df = df[df['지역'] != '전국']

            df_sorted = df.sort_values(['지역', '연도'])
            df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff().fillna(0)

            df_sorted['인구'] = df_sorted['인구'].map('{:,.0f}'.format)
            df_sorted['증감_표시'] = df_sorted['증감'].map('{:,.0f}'.format)

            top_diff = df_sorted.sort_values('증감', ascending=False).head(100)

            def highlight_diff(val):
                color = ''
                if val > 0:
                    color = f'background-color: rgba(0, 0, 255, {min(0.5 + abs(val)/top_diff["증감"].max(), 1):.2f})'
                elif val < 0:
                    color = f'background-color: rgba(255, 0, 0, {min(0.5 + abs(val)/abs(top_diff["증감"].min()), 1):.2f})'
                return color

            styled_df = top_diff[['연도', '지역', '인구', '증감_표시']].style.apply(
                lambda x: [highlight_diff(v) for v in top_diff['증감']], axis=1
            ).set_properties(**{'text-align': 'center'})

            st.dataframe(styled_df)

        # 5. 시각화
        with tabs[4]:
            df.replace('-', 0, inplace=True)
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0).astype(int)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce').astype(int)

            region_df = df[df['지역'] != '전국'].copy()

            region_name_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
                '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam',
                '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            region_df['region_eng'] = region_df['지역'].map(region_name_map)

            pivot_df = region_df.pivot_table(index='연도', columns='region_eng', values='인구', aggfunc='sum')
            pivot_df = pivot_df.sort_index()

            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(12, 6))
            pivot_df.fillna(0).div(1000).plot.area(ax=ax, colormap='tab20', linewidth=0)

            ax.set_title('Population Trend by Region (Stacked Area)')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population (Thousands)')
            ax.legend(title='Region', bbox_to_anchor=(1.05, 1), loc='upper left')

            st.subheader("📊 Stacked Area Chart: Population by Region")
            st.pyplot(fig)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()