import requests

def fetch_indicators_data():
    try:
        # 发送 GET 请求
        response = requests.get("http://localhost:8111/indicators")
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        if(data.get("army") == "tank"):
            crew_total = data.get("crew_total")
            crew_current = data.get("crew_current")
            driver_state = data.get("driver_state")
            gunner_state = data.get("gunner_state")
            return 1, crew_total, crew_current, driver_state, gunner_state
        elif(data.get("army") == "air"):
            resp = requests.get("http://localhost:8111/state")
            resp.raise_for_status()  # 检查请求是否成功
            dt = resp.json()
            if(dt.get("Ny") != None):
                g = abs(dt.get("Ny"))
            else:
                g = 0

            return 2, g, None, None, None

    except requests.exceptions.RequestException as e:
        return None, None, None, None
    except ValueError as e:
        return None, None, None, None


# 主逻辑
def run_data_fetcher(tankhit=5,tankdie=100,g_force=10):
    try:
        # 获取数据
        type_, var2, crew_current, driver_state, gunner_state = fetch_indicators_data()

        if type_ == 1:
            if var2 is not None and crew_current is not None and driver_state is not None and gunner_state is not None:
                # 计算 crew_deal
                crew_deal = var2 - crew_current

                # 判断条件：driver_state 和 gunner_state 均为 1，且 crew_deal 为 0
                if driver_state == 1 and gunner_state == 1 and crew_current < 2:
                    vehicles_deal = 1
                else:
                    vehicles_deal = 0

                #print(f"crew_deal: {crew_deal}/vehicles_deal: {vehicles_deal}")

                # 计算 s_a
                sa = 20 + tankhit * crew_deal + tankdie * vehicles_deal

                return sa

            else:
                print("Failed to extract driver_state or gunner_state.")

        elif type_ == 2:
            if var2 is not None:
                if var2 > 20:
                    var2 = 20

                # 计算 s_a
                sa = 20 + g_force * var2 #0-20

                #print(f"G: {var2}/sa: {sa}")

                return sa

            else:
                print("Failed to extract Ny.")

    except KeyboardInterrupt:
        print("Data fetcher stopped by user.")