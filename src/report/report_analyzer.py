import os
import pandas as pd
import matplotlib.pyplot as plt
import report.balance as balance
import report.income as income

class ReportAnalyzer():
    def __init__(self, args, data_path):
        self.data_path = data_path
        self.single_stock = True
        if (len(args.stock) > 1):
            self.single_stock = False
        self.args = args

        self.balance_df = []
        self.income_df = []
        self.balance_analyzer = []
        self.income_analyzer = []

    def estimate_profitability(self):
        income_es = pd.DataFrame(self.income_df[0].loc['营业利润(万元)'])
        income_es['资产总计(万元)'] = self.balance_df[0].loc['资产总计(万元)']
        income_es['净利润(万元)'] = self.income_df[0].loc['净利润(万元)']
        income_es['负债合计(万元)'] = self.balance_df[0].loc['负债合计(万元)']
        income_es['净资产(万元)'] = self.balance_df[0].loc['所有者权益(或股东权益)合计(万元)']

        income_es['总资产报酬率'] = income_es['营业利润(万元)'] / income_es['资产总计(万元)']
        income_es['净资产报酬率'] = income_es['净利润(万元)'] / income_es['净资产(万元)']
        income_es.T.to_csv("income_estimate.csv", sep=',', encoding='utf-8-sig')
        print(income_es.T)

    def estimate_asset(self):
        #print(self.asset_df.loc['流动资产合计(万元)'])
        df_asset_es = pd.DataFrame(self.balance_df[0].loc['资产总计(万元)'])
        df_asset_es['存货(万元)'] = self.balance_df[0].loc['存货(万元)']
        df_asset_es['流动资产合计(万元)'] = self.balance_df[0].loc['流动资产合计(万元)']
        df_asset_es['负债合计(万元)'] = self.balance_df[0].loc['负债合计(万元)']
        df_asset_es['流动负债合计(万元)'] = self.balance_df[0].loc['流动负债合计(万元)']
        df_asset_es['实收资本(或股本)(万元)'] = self.balance_df[0].loc['实收资本(或股本)(万元)']

        # 营运资金
        df_asset_es['营运资金'] = df_asset_es['流动资产合计(万元)'] - df_asset_es['流动负债合计(万元)']
        # 酸性测试
        df_asset_es['酸性测试'] = ['True' if x>0 else 'False' for x in df_asset_es['营运资金'] - df_asset_es['存货(万元)']]
        # 每股清算价值 ~ 流动资产价值
        df_asset_es['流动资产价值'] = df_asset_es['营运资金'] / df_asset_es['实收资本(或股本)(万元)']
        # 每股账面价值
        df_asset_es['账面价值'] = (df_asset_es['资产总计(万元)'] - df_asset_es['负债合计(万元)']) / df_asset_es['实收资本(或股本)(万元)']
        # 资产负债率
        df_asset_es['资产负债率'] = (df_asset_es['负债合计(万元)'] / df_asset_es['资产总计(万元)'])
        df_asset_es.T.to_csv("assert_estimate.csv", sep=',', encoding='utf-8-sig')
        print(df_asset_es.T)

    def prepare(self):
        for stock in self.args.stock:
            balance_filename = "zcfzb" + stock + ".csv"
            income_filename = "lrb" + stock + ".csv"
            balance_datafile = os.path.join(self.data_path, balance_filename)
            income_datafile = os.path.join(self.data_path, income_filename)

            if os.access(balance_datafile, os.R_OK) and os.access(income_datafile, os.R_OK):
                self.balance_analyzer.append(balance.BalanceSheetAnalyzer(balance_datafile))
                self.income_analyzer.append(income.IncomeStatementAnalyzer(income_datafile))
            else:
                print("Can't find {} and {}".format(self.balance_datafile, self.income_datafile))
                os._exit(0)

    def compare_multi_stock_by_value(self, stocks_df, title):
        self.multi_stocks_df = pd.DataFrame(stocks_df[0].index)
        self.multi_stocks_df = self.multi_stocks_df.set_index(['报告日期'])

        # 保存多只股票最近一年的资产负债表/利润表数据
        filter_condition = [True] * len(stocks_df[0]['2018-12-31'])
        for i in range(len(self.args.stock)):
            s = self.args.stock[i]
            self.multi_stocks_df[s] = stocks_df[i]['2018-12-31']
            filter_condition &= self.multi_stocks_df[s] > 10000
            #print(filter_condition)
        #print(self.multi_stocks_asset_df)

        # 修正x轴标签过长，删除其中包含的'(万元)'字段
        df_for_plot = self.multi_stocks_df[filter_condition]
        index = pd.Series(df_for_plot.index)
        index.replace(to_replace='\(万元\)', value=' ', regex=True, inplace=True)
        df_for_plot.index = index
        #print(index)
        #print(df_for_plot)

        plt.rcParams['font.sans-serif'] = ['SimHei']
        dp = df_for_plot.plot(kind='bar', figsize=(8,6))
        #df_for_plot.index = df_for_plot.index.strip()
        plt.title(title)
        dp.set_xlabel("项目")
        dp.set_ylabel("价值（万元）")
        dp.set_xticks(range(len(df_for_plot.index)))
        dp.set_xticklabels(df_for_plot.index, rotation=90)
        #plt.tight_layout()
        plt.subplots_adjust(wspace=0.6, hspace=0.6, left=0.1, bottom=0.22, right=0.96, top=0.96)
        #plt.subplot_tool()
        plt.show()

    def analize(self):
        for i in range(len(self.args.stock)):
            self.balance_df.append(self.balance_analyzer[i].numberic_df)
            self.income_df.append(self.income_analyzer[i].numberic_df)

        if (self.single_stock):
            if (self.args.option == 'balance'):
                self.balance_analyzer[0].analize()
                self.estimate_asset()
            elif (self.args.option == 'income'):
                self.income_analyzer[0].analize()
                self.estimate_profitability()
            else:
                print("Invalid option !")
        else:
            if (self.args.option == 'balance'):
                self.compare_multi_stock_by_value(self.balance_df, '资产负债表')
            elif (self.args.option == 'income'):
                self.compare_multi_stock_by_value(self.income_df, '利润表')
            else:
                print("Invalid option !")

    def start(self):
        self.prepare()
        self.analize()
