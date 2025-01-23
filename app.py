# coding=<utf-8>
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import pandas as pd
import os

app = Flask(__name__)

# CSV 파일 경로
hospital_csv_file_path = '지역별병원데이터.csv'
disease_csv_file_path = 'diseaseOfSubject.csv'

def generate_substrings(input_string, min_length=2):
    """입력된 문자열에서 가능한 모든 부분 문자열을 생성합니다."""
    length = len(input_string)
    return [input_string[i:j+1] for i in range(length) for j in range(i + min_length - 1, length)]

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/submitHealthInfo", methods=['GET', 'POST'])
def submit_health_info():
    if request.method == 'POST':
        # 입력 받은 사용자 데이터
        name = request.form['name']
        per_num = request.form['per_num']
        sex = request.form['sex']
        disease = request.form['disease']
        postcode = request.form['postcode']
        road_Address = request.form['roadAddress']
        detailAddress = request.form['detailAddress']

        # 상세주소에서 시와 구 정보 추출
        address_parts = road_Address.split()
        if len(address_parts) > 1:
            city = address_parts[0]
            gu = address_parts[1]
        else:
            return "도로명 주소를 정확히 입력해주세요."

        try:
            # 병원 정보 CSV 파일 읽기
            hospital_df = pd.read_csv(hospital_csv_file_path, on_bad_lines='skip', quotechar='"', skipinitialspace=True)
            # 질병 정보 CSV 파일 읽기
            disease_df = pd.read_csv(disease_csv_file_path, encoding='cp949', on_bad_lines='skip', quotechar='"', skipinitialspace=True)
        except pd.errors.ParserError as e:
            return f"CSV 파일 읽기 오류: {e}"

          # 병명이 포함된 과목 열의 데이터 추출
        clinic_sub = disease_df.loc[disease_df['질병'].str.contains(disease, case=False, na=False), '과목'].tolist()

        # 각 과목에 대한 모든 부분 문자열 리스트 생성
        substrings = [sub for item in clinic_sub for sub in generate_substrings(item, 2)]

        # 주소와 과목 정보가 모두 포함된 병원 데이터 필터링
        filtered_df = hospital_df[
            (hospital_df['Address'].str.contains(city) & 
             hospital_df['Address'].str.contains(gu)) &
            (hospital_df['Clinic Name'].apply(lambda x: any(sub in x for sub in substrings)))
        ]

         # DataFrame을 HTML로 변환하고 라디오 버튼 추가
        html_table = filtered_df.to_html(classes='data', header="true", index=False, escape=False)
        soup = BeautifulSoup(html_table, 'html.parser')

        # 헤더에 'Select' 열 추가
        header = soup.find('tr')
        new_th = soup.new_tag('th')
        new_th.string = 'Select'
        header.insert(0, new_th)

        # 각 행에 라디오 버튼 추가
        for i, row in enumerate(soup.find_all('tr')[1:]):  # 첫 번째 행은 헤더이므로 건너뜁니다.
            radio_button = soup.new_tag('input', type='radio', attrs={'name': 'selected_hospital', 'value': str(i)})
            new_td = soup.new_tag('td')
            new_td.append(radio_button)
            row.insert(0, new_td)  # 첫 번째 열에 삽입합니다.

        modified_html_table = str(soup)

        # 결과를 HTML 테이블로 렌더링
        return render_template('result.html', tables=[modified_html_table],
                               name=name, per_num=per_num, sex=sex, disease=disease,
                               postcode=postcode, road_Address=road_Address, detailAddress=detailAddress)
        
    return render_template('index.html')


if __name__ == '__main__':
    # 개발 서버를 외부에서 접속 가능하도록 설정
    app.run(host='0.0.0.0', port=5000, debug=True)