#
# Python Script with Base Class
# for Event-Based Backtesting
#
# Python for Algorithmic Trading
# (c) Dr. Yves J. Hilpisch
# The Python Quants GmbH
#
import numpy as np
import pandas as pd
from pylab import mpl, plt
import os
currentPath = os.getcwd()





class BacktestBase(object):
    ''' 거래 전략을 가지고 이벤트 기반 백테스트를 하기 위한 기저 클래스
    속성
    ==========
    symbol: str
        사용할 TR RIC (금융 수단)
    start: str
        데이터를 선택한 부분의 시작 일자
    end: str
        데이터를 선택한 부분의 종료 일자
    amount: float
        한 번 투자하거나 거래당 투자할 금액
    ftc: float
        거래당 고정 거래비용(매수 또는 매도)
    ptc: float
        거래당 비례 거래비용(매수 또는 매도)
    
    메소드
    =======
    get_data:
        기본 데이터 집합을 검색해(인출해) 준비한다.
    plot_data:
        종목코드에 대한 종가를 그려 낸다.
    get_date_price:
        주어진 봉에 대한 일자와 가격을 반환한다.
    print_balance:
        현재 (현금) 잔고를 프린트해 낸다.
    print_net_wealth:
        현재 순 자산을 프린트해 낸다.
    place_buy_order:
        매수 주문을 넣는다.
    place_sell_order:
        매도 주문을 넣는다.
    close_out:
        롱 포지션이나 숏 포지션을 닫는다.
    '''

    def __init__(self, amount, verbose=True):
        #self.symbol = symbol
        #self.start = start
        #self.end = end
        self.initial_amount = amount
        self.amount = amount
        #self.ftc = ftc
        #self.ptc = ptc
        self.units = 0
        self.position = 0
        self.trades = 0
        self.verbose = verbose
        self.col = ''
        self.get_data()

    def get_data(self):
        ''' 데이터를 검색해(인출해) 준비해둔다.
        '''
        data = pd.read_csv('/workspaces/Americano/americano/engine/test_stg_ash/raw_data.csv', index_col = 0, encoding='CP949')
        col = list(data.columns)
        col.reverse()

        mean_col = [f'{i}_mean_acc' for i in col]
        mean_data = pd.DataFrame(columns=mean_col)

        am_col = [f'{i}_AM' for i in col]
        am_data = pd.DataFrame(columns=am_col)

        rm_col = [f'{i}_RM' for i in col]
        rm_data = pd.DataFrame(columns=rm_col)

        del mean_data['close_mean_acc']

        for i in col:
            # 누적 수익률
            df_PROFIT = data[i].pct_change()
            data[f'{i}_acc'] = (1+df_PROFIT).cumprod()-1

            # log 누적 수익률
            df_LOG_PROFIT = np.log(df_PROFIT+1)
            data[f'{i}_log_acc'] = df_LOG_PROFIT.cumsum()
            data.fillna(0,inplace=True)

            # 필요없는 부분 except 처리
            try:
                data = pd.concat([data, mean_data[f'{i}_mean_acc']],axis=1)
            except:
                pass
            finally:
                data = pd.concat([data, am_data[f'{i}_AM']],axis=1)
                data = pd.concat([data, rm_data[f'{i}_RM']],axis=1)

            # 평균 누적 수익률
            for j in range(0, len(data)):   
                try:
                    data[f'{i}_mean_acc'][j] = (data[f'{i}_acc'][j] - data['close_acc'][j])
                except:
                    pass
                if j == 0:
                    continue
                else:
                    # 절대 모멘텀
                    data[f'{i}_AM'][j] = ((data[i][j] / data[i][j-1]) - 1)
                    if i == 'close':
                        pass
                    else:
                        # 상대 모멘텀
                        data[f'{i}_RM'][j] = (data[f'{i}_AM'][j] - data['close_AM'][j])

            data.fillna(0,inplace=True)
        col_name = data.columns[0:11]
        #data = data[col_name]
        self.data_price = data[col_name]
        self.data = data

    def plot_data(self, cols=None):
        ''' 종목코드의 종가를 표시한다.
        '''
        if cols is None:
            cols = ['price']
        self.data[cols].plot(figsize=(10, 6), title=self.symbol)

    def get_date_price(self, bar, col):
        ''' 봉에 대한 일자와 가격을 반환한다.
        '''
        date = str(self.data.index[bar])[:10]
        price = self.data[col].iloc[bar]
        return date, price

    def print_balance(self, bar, col):
        ''' 현재 현금잔고 정보를 프린트한다.
        '''
        date, price = self.get_date_price(bar, col)
        print(f'{date} | current balance {self.amount:.2f}')

    def print_net_wealth(self, bar, col):
        ''' 현재 현금잔고 정보를 프린트한다.
        '''
        date, price = self.get_date_price(bar, col)
        net_wealth = self.units * price + self.amount
        print(f'{date} | current net wealth {net_wealth:.2f}')

    def place_buy_order(self, bar, col, units, amount):
        ''' 매수 주문을 넣는다.
        '''
        date, price = self.get_date_price(bar, col)
        print('units : ',units ,'/ amount : ', amount)
        if bar == 0:
            units = int(amount / price)
        buy_price = (units * price)
        self.amount -= buy_price
        self.units += units
        self.trades += 1
        print('amount : ', amount)
        print(f'<매수> 잔고 : {self.amount} | 매수 금액 : {buy_price} | 잔여 수량 : {self.units} | 수량 : {units} | trades : {self.trades}')
        if self.verbose:
            print(f'{date} | buying {units} units at {price:.2f}')
            self.print_balance(bar, col)
            self.print_net_wealth(bar, col)

    def place_sell_order(self, bar, col, units, amount):
        ''' 매도 주문을 넣는다.
        '''
        date, price = self.get_date_price(bar, col)
        print('units : ',units ,'/ amount : ', amount)
        if bar == 0:
            units = int(amount / price)
        sell_price = (units * price)
        self.amount += sell_price
        self.units -= units
        self.trades += 1
        
        print('amount : ', amount)
        print(f'<매도> 잔고 : {self.amount} | 매도 금액 : {sell_price} | 잔여 수량 : {self.units} | 수량 : {units} | trades : {self.trades}')
        if self.verbose:
            print(f'{date} | selling {units} units at {price:.2f}')
            self.print_balance(bar, col)
            self.print_net_wealth(bar, col)

    def close_out(self, bar, col):
        ''' 롱 포지션이나 숏 포지션을 닫는다.
        '''
        date, price = self.get_date_price(bar, col)
        self.amount += self.units * price
        self.units = 0
        self.trades += 1
        if self.verbose:
            print(f'{date} | inventory {self.units} units at {price:.2f}')
            print('=' * 55)
        print('Final balance   [W] {:.2f}'.format(self.amount))
        perf = ((self.amount - self.initial_amount) /
                self.initial_amount * 100)
        print('Performance [%] {:.2f}'.format(perf))
        print('Trades Executed [#] {}'.format(self.trades))
        print('=' * 55)


if __name__ == '__main__':
    #col = ['A293490','A263750','A259960','A251270','A194480','A192080','A181710','A112040','A078340','A036570']
    bb = BacktestBase(10000000)
    #print(bb.data.info())
    #print(bb.data.tail())
    #bb.plot_data()
    #plt.savefig('../../images/ch06/backtestbaseplot.png')