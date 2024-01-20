import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table, callback, Input, Output

from matplotlib import font_manager, rc
# font_path = 'C:/Windows/Fonts/malgun.ttf'
# font_name = font_manager.FontProperties(fname = font_path).get_name()
# rc('font', family=font_name)

def mk_graph_data(df):
    visual_df = pd.DataFrame(df.groupby(["주소(시도)", "카테고리", "기술스택"]).size())
    visual_df = visual_df.reset_index()
    visual_df = visual_df.rename(columns = {0 : "채용공고수"})
    
    final_df = None
    groups = visual_df.groupby(["주소(시도)", "카테고리"])
    
    for idx, group in groups:
        if final_df is None:
            final_df = group.sort_values("채용공고수", ascending = False)[:10].copy()
        elif len(group) > 10:
            final_df = pd.concat([final_df, group.sort_values("채용공고수", ascending = False)[:10]])
        else:
            final_df = pd.concat([final_df, group])
            
    return final_df

csdf = pd.read_csv("시장조사_240102_csdf.csv")

show_cols = ["제목", "회사명", "최소경력", "최대경력", "주소(시도)", "주소(시군구)", "카테고리", "기술스택"]

app = Dash()
app.layout = html.Div([
    html.Div(children = "경력 설정"),
    dcc.RangeSlider(min(csdf["최소경력"]), max(csdf["최대경력"]), 1, value = [0, 40], id = "ca_minmax"),
    
    html.Div(children = "주소 설정"),
    dcc.Dropdown(csdf["주소(시도)"].unique(), value = "서울", multi = True, id = "first_addr"),
    
    html.Div(children = "상세 주소 설정"),
    dcc.Dropdown(id = "second_addr", multi = True),
    
    html.Div(children = "카테고리 설정"),
    dcc.Dropdown(options = csdf["카테고리"].unique(), id = "cate", multi = True),
    
#     html.Div(children = "기술스택 검색"),
#     dcc.Input(id = "search_query", type = "text"),
    
    html.Hr(),
    dash_table.DataTable(page_size = 5,
                         id = "result_table"),
    dcc.Graph(id = "result_graph")
], style = {"marginBottom" : 50, "marginTop" : 50})

@callback(
    Output("second_addr", "options"),
    Input("first_addr", "value")
)
def update_options(value):
    return list(csdf[csdf["주소(시도)"].map(lambda x: x in value)].dropna(subset = ["주소(시군구)"])["주소(시군구)"].unique())

@callback(
    Output("result_table", "data"),
    Input("ca_minmax", "value"),
    Input("first_addr", "value"),
    Input("second_addr", "value"),
    Input("cate", "value"),
#     Input("search_query", "value")
)
def update_table(minmax, first_addr, second_addr, cate):
    tmp_table = csdf[(csdf["최소경력"] >= minmax[0]) & (csdf["최대경력"] <= minmax[1])][show_cols]
#     if query:
#         query = map(lambda x: x.strip().lower(), query.split(","))
        
    conditions = [
        bool(first_addr),
        bool(second_addr),
        bool(cate),
#         bool(query)
    ]
        
    filtered_table = tmp_table.copy()
    if conditions[0]:
        filtered_table = filtered_table[filtered_table["주소(시도)"].isin(first_addr if type(first_addr) == list else [first_addr])]
        
    if conditions[1]:
        filtered_table = filtered_table[filtered_table["주소(시군구)"].isin(second_addr)]
        
    if conditions[2]:
        filtered_table = filtered_table[filtered_table["카테고리"].isin(cate)]
        
#     if conditions[3]:
#         filtered_table = filtered_table[filtered_table["기술스택"].map(lambda x: x.strip().lower() in query)]
        
    return filtered_table.to_dict("records")

@callback(
    Output("result_graph", "figure"),
    Input("result_table", "data"))
def update_graph(df):
    df = pd.DataFrame(df)
    df = mk_graph_data(df)
    fig = px.sunburst(data_frame = df, path = ["주소(시도)", "카테고리", "기술스택"],
                  values = "채용공고수")
    return fig

if __name__ == "__main__":
    app.run_server(debug = True, use_reloader = False, host='0.0.0.0')
