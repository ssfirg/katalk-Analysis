import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl # 기본 설정 만지는 용도
import seaborn as sns # 시각화 패키지
import matplotlib.cm as cm # 컬러맵 생성을 위한 패키지
import matplotlib.colors as colors # 컬러맵 생성을 위한 패키지
plt.rc('font',family= 'NanumGothic') # 한글 폰트 설정
mpl.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지


class KatalkAnalyzer: #카톡 분석기

    def __init__(self):
        return


    def katalk_msg_parse(self, file_path): #카톡 파일 읽기
        my_katalk_data = list()
        katalk_msg_pattern = "[0-9]{4}[년.] [0-9]{1,2}[월.] [0-9]{1,2}[일.] 오\S [0-9]{1,2}:[0-9]{1,2},.*:"
        date_info = "[0-9]{4}년 [0-9]{1,2}월 [0-9]{1,2}일 \S요일"
        in_out_info = "[0-9]{4}[년.] [0-9]{1,2}[월.] [0-9]{1,2}[일.] 오\S [0-9]{1,2}:[0-9]{1,2}:.*"

        for line in open(file_path, 'rt', encoding = "UTF8"):
            if re.match(date_info, line) or re.match(in_out_info, line):
                continue
            elif line == '\n':
                continue
            elif re.match(katalk_msg_pattern, line):
                line = line.split(",")
                date_time = line[0]
                user_text = line[1].split(" : ", maxsplit=1)
                user_name = user_text[0].strip()
                text = user_text[1].strip()
                my_katalk_data.append({'date_time': date_time,
                                    'user_name': user_name,
                                    'text': text
                                    })

            else:
                if len(my_katalk_data) > 0:
                    my_katalk_data[-1]['text'] += "\n"+line.strip()

        my_katalk_df = pd.DataFrame(my_katalk_data)

        return my_katalk_df
    
    def process_data(self, df, start_date= None, end_date= None): #데이터 전처리
        df['date_time'] = df['date_time'].str.replace('오전', 'AM')
        df['date_time'] = df['date_time'].str.replace('오후', 'PM')
        try:
            df['date_time'] = pd.to_datetime(df['date_time'], format= "%Y년 %m월 %d일 %p %I:%M")
        except:
            df['date_time'] = pd.to_datetime(df['date_time'], format= "%Y. %m. %d. %p %I:%M") #-> 형식에 맞춰서 바꿔줘야함

        df['요일'] = df['date_time'].dt.day_name()
        df['year'] = df['date_time'].dt.year
        df['month'] = df['date_time'].dt.month
        df['day'] = df['date_time'].dt.day
        df['hour'] = df['date_time'].dt.hour
        df.set_index('date_time',inplace=True)
        df = df.loc[start_date:end_date]
        df['text_len'] = df['text'].apply(lambda x: len(x))
        return df
    
    def modify(self, df): #데이터 수정
        temp11 =df.groupby(['year','month','day'])['user_name'].value_counts()
        temp22 = pd.DataFrame(temp11)
        temp22 = temp22.unstack()
        temp22.columns = temp22.columns.get_level_values('user_name')
        temp22.columns.name=None
        return temp22
    
    def modify_2(self, df): #데이터 수정 카톡 길이 기준
        temp = df.groupby(['year','month','day','user_name'])['text_len'].sum().unstack()
        temp.columns.name=None
        return temp 
    
    
    def plot_cumulative_barh(self, df, group_columns): #누적 막대 그래프
        grouped_data = df.groupby(group_columns).sum()
        cumulative_values = grouped_data.cumsum()
        colors = sns.color_palette('pastel', len(cumulative_values))

        total_values = cumulative_values.iloc[-1]
        total_sum = total_values.sum()

        plt.figure(figsize=(10, 6))
        for i in range(len(cumulative_values)):
            if i == 0:
                plt.barh(df.columns, grouped_data.iloc[i], label=f'{grouped_data.index[i]}', color=colors[i])
            else:
                plt.barh(df.columns, grouped_data.iloc[i], left=cumulative_values.iloc[i-1], label=f'{grouped_data.index[i]}', color=colors[i])
        
        title = f'{df.index[0][0]}년 {df.index[0][1]}월 {df.index[0][2]}일부터 {df.index[-1][1]}월 {df.index[-1][2]}일까지의 채팅수'
        plt.title(title, pad=15)
        plt.legend()

        for i, val in enumerate(total_values):
            percentage = (val / total_sum) * 100
            plt.text(val, i, f'{percentage:.1f}%', va='center', fontsize=8)

        plt.show()


    def stat_hour(self, temp, title): #시간대별 평균 카톡 횟수
        # 정규화된 높이 값 계산
        normalized_values = (temp - temp.min()) / (temp.max() - temp.min())
        # 컬러맵 생성
        colormap = sns.color_palette("Set2", as_cmap=True)
        # 높이 값에 따라 색상 매핑
        color_mapped = colormap(normalized_values)
        # Normalize 객체 생성
        norm = colors.Normalize(vmin=0, vmax=1)
        # 색상을 정규화된 값에 따라 조정
        color_adjusted = colormap(norm(normalized_values))
        # 막대 그래프 그리기
        plt.bar(temp.index, temp, color=color_adjusted)
        plt.title(title, pad = 15)
        # 그래프 출력
        plt.show()

    def analyze(self, df): #분석
        df3 = self.modify(df)
        df4 = df3[df3.sum().sort_values(ascending=False).index]
        self.plot_cumulative_barh(df4, ['year','month'])
    

        temp = df['hour'].value_counts()
        days = len(df.groupby(['year','month','day']).nunique().index)
        temp = temp/days
        temp.sort_index(inplace=True)
        self.stat_hour(temp, '시간대별 평균 카톡 횟수')

        temp2 = df.groupby(['year','month','day','요일']).nunique()
        temp3 = df['요일'].value_counts()/temp2.index.get_level_values('요일').value_counts()
        temp3 =temp3.reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
        self.stat_hour(temp3, "요일별 평균 카톡 횟수")

        df3.cumsum(axis=0).ffill(axis=0).rank(axis=1).plot(colormap='turbo',figsize=(15,6))
        df3.cumsum().fillna(method='ffill').plot(figsize=(15,6),
                                        title=f'{df3.index[0][0]}년 {df3.index[0][1]}월 {df3.index[0][2]}일부터 {df3.index[-1][1]}월 {df3.index[-1][2]}일까지의 채팅빈도수')

if __name__=="__main__":
    ka = KatalkAnalyzer()
    path = "" #카톡 파일 경로
    start_date = "2023-04-01" #시작 날짜
    end_date = "2023-06-30"   #끝 날짜
    df = ka.katalk_msg_parse(path) #카톡 파일 읽기
    df2 = ka.process_data(df, start_date= start_date, end_date= end_date)
    ka.analyze(df2) #분석