import os 
from datetime import datetime
import pandas as pd
import numpy as np

class Momentum():

    def data_preprocessing(sample, ticker, base_date):   
        sample['code'] = ticker # 종목코드 추가
        sample = sample[sample['date'] >= base_date][['date','code','close_price']].copy() # 기준일자 이후 데이터 사용
        sample.reset_index(inplace= True, drop= True)
        # 기준년월 
        sample['STD_YM'] = sample['date'].map(lambda x : datetime.strptime(x,'%Y-%m-%d').strftime('%Y-%m')) 
        sample['1D_RET'] = 0.0 # 수익률 컬럼
        ym_keys = list(sample['STD_YM'].unique()) # 중복 제거한 기준년월 리스트
        return sample, ym_keys

    def create_trade_book(sample, sample_codes):
        book = pd.DataFrame()
        book = sample[sample_codes].copy()
        book['STD_YM'] = book.index.map(lambda x : datetime.strptime(x,'%Y-%m-%d').strftime('%Y-%m'))
        for c in sample_codes:
            book['p '+c] = ''
            book['r '+c] = ''
        return book

    # 상대모멘텀 tradings
    def tradings(book, s_codes):
        std_ym = ''
        buy_phase = False
        # 종목코드별 순회
        for s in s_codes : 
            print(s)
            # 종목코드 인덱스 순회
            for i in book.index:
                # 해당 종목코드 포지션을 잡아준다. 
                if book.loc[i,'p '+s] == '' and book.shift(1).loc[i,'p '+s] == 'ready ' + s:
                    std_ym = book.loc[i,'STD_YM']
                    buy_phase = True
                # 해당 종목코드에서 신호가 잡혀있으면 매수상태를 유지한다.
                if book.loc[i,'p '+s] == '' and book.loc[i,'STD_YM'] == std_ym and buy_phase == True : 
                    book.loc[i,'p '+s] = 'buy ' + s
                
                if book.loc[i,'p '+ s] == '' :
                    std_ym = None
                    buy_phase = False
        return book

    def multi_returns(book, s_codes):
        # 손익 계산
        rtn = 1.0
        buy_dict = {}
        num = len(s_codes)
        sell_dict = {}
        
        for i in book.index:
            for s in s_codes:
                if book.loc[i, 'p ' + s] == 'buy '+ s and \
                book.shift(1).loc[i, 'p '+s] == 'ready '+s and \
                book.shift(2).loc[i, 'p '+s] == '' :     # long 진입
                    buy_dict[s] = book.loc[i, s]
    #                 print('진입일 : ',i, '종목코드 : ',s ,' long 진입가격 : ', buy_dict[s])
                elif book.loc[i, 'p '+ s] == '' and book.shift(1).loc[i, 'p '+s] == 'buy '+ s:     # long 청산
                    sell_dict[s] = book.loc[i, s]
                    # 손익 계산
                    rtn = (sell_dict[s] / buy_dict[s]) -1
                    book.loc[i, 'r '+s] = rtn
                    print('개별 청산일 : ',i,' 종목코드 : ', s , 'long 진입가격 : ', buy_dict[s], ' |  long 청산가격 : ',\
                        sell_dict[s],' | return:', round(rtn * 100, 2),'%') # 수익률 계산.
                if book.loc[i, 'p '+ s] == '':     # zero position || long 청산.
                    buy_dict[s] = 0.0
                    sell_dict[s] = 0.0


        acc_rtn = 1.0        
        for i in book.index:
            rtn  = 0.0
            count = 0
            for s in s_codes:
                if book.loc[i, 'p '+ s] == '' and book.shift(1).loc[i,'p '+ s] == 'buy '+ s: 
                    # 청산 수익률계산.
                    count += 1
                    rtn += book.loc[i, 'r '+s]
            if (rtn != 0.0) & (count != 0) :
                acc_rtn *= (rtn /count )  + 1
                print('누적 청산일 : ',i,'청산 종목수 : ',count, \
                    '청산 수익률 : ',round((rtn /count),4),'누적 수익률 : ' ,round(acc_rtn, 4)) # 수익률 계산.
            book.loc[i,'acc_rtn'] = acc_rtn
        print ('누적 수익률 :', round(acc_rtn, 4))
