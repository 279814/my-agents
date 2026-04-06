"""
比特币价格显示应用 - 优化版
功能：实时显示比特币当前价格、24小时变化趋势，并提供刷新功能
技术栈：Streamlit + requests + tenacity + CoinGecko API
"""

import streamlit as st
import requests
import time
from datetime import datetime
import json
import logging
import os
from typing import Optional, Dict, Any
import tenacity

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="比特币价格追踪器",
    page_icon="₿",
    layout="centered"
)


# ==================== 配置类 ====================
class Config:
    """应用配置"""
    API_URL = "https://api.coingecko.com/api/v3/simple/price"
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3
    CACHE_TTL = 30  # 数据缓存时间（秒）

    @staticmethod
    def get_api_params():
        return {
            'ids': 'bitcoin',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }

    @staticmethod
    def get_headers():
        """获取请求头"""
        return {
            'User-Agent': 'BitcoinPriceTracker/1.0',
            'Accept': 'application/json'
        }


# ==================== 自定义异常 ====================
class BitcoinPriceError(Exception):
    """比特币价格相关异常基类"""
    pass


class APINotAvailableError(BitcoinPriceError):
    """API不可用异常"""
    pass


class InvalidDataError(BitcoinPriceError):
    """数据格式错误异常"""
    pass


class NetworkError(BitcoinPriceError):
    """网络错误异常"""
    pass


# ==================== API客户端 ====================
class BitcoinAPIClient:
    """比特币API客户端"""

    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update(self.config.get_headers())

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(Config.MAX_RETRIES),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(
            (requests.exceptions.Timeout,
             requests.exceptions.ConnectionError)
        ),
        reraise=True
    )
    def fetch_bitcoin_price(self) -> Dict[str, Any]:
        """
        从CoinGecko API获取比特币价格数据
        返回: dict - 包含价格和24小时变化的数据
        """
        try:
            logger.info("开始获取比特币价格数据")

            response = self.session.get(
                self.config.API_URL,
                params=self.config.get_api_params(),
                timeout=self.config.REQUEST_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            # 数据验证
            self._validate_response_data(data)

            bitcoin_data = data['bitcoin']
            result = {
                'current_price': bitcoin_data['usd'],
                'price_change_24h': bitcoin_data['usd_24h_change'],
                'last_updated': bitcoin_data['last_updated_at']
            }

            logger.info(f"成功获取比特币价格: ${result['current_price']}")
            return result

        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            raise NetworkError("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            logger.error("网络连接错误")
            raise NetworkError("网络连接错误，请检查网络设置")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
            logger.error(f"HTTP错误: {status_code}")
            if status_code == 429:
                raise APINotAvailableError("API请求过于频繁，请稍后再试")
            else:
                raise APINotAvailableError(f"API服务暂时不可用 (HTTP {status_code})")
        except json.JSONDecodeError:
            logger.error("API响应JSON解析错误")
            raise InvalidDataError("API响应格式错误")
        except Exception as e:
            logger.error(f"获取数据时发生未知错误: {str(e)}")
            raise BitcoinPriceError(f"获取数据失败: {str(e)}")

    def _validate_response_data(self, data: Dict) -> None:
        """验证API响应数据"""
        if 'bitcoin' not in data:
            raise InvalidDataError("API响应中未找到比特币数据")

        bitcoin_data = data['bitcoin']
        required_fields = ['usd', 'usd_24h_change', 'last_updated_at']

        for field in required_fields:
            if field not in bitcoin_data:
                raise InvalidDataError(f"API响应缺少必要字段: {field}")

        # 验证数据类型
        if not isinstance(bitcoin_data['usd'], (int, float)):
            raise InvalidDataError("价格数据格式错误")
        if not isinstance(bitcoin_data['usd_24h_change'], (int, float)):
            raise InvalidDataError("涨跌幅数据格式错误")


# ==================== 数据处理工具 ====================
class DataProcessor:
    """数据处理工具类"""

    @staticmethod
    def format_price(price: float) -> str:
        """格式化价格显示"""
        if price >= 1000:
            return f"${price:,.2f}"
        else:
            return f"${price:.2f}"

    @staticmethod
    def format_change(change: Optional[float]) -> str:
        """格式化涨跌幅显示"""
        if change is None:
            return "N/A"

        change_str = f"{change:+.2f}%"
        if change > 0:
            return f"📈 {change_str}"
        elif change < 0:
            return f"📉 {change_str}"
        else:
            return f"➡️ {change_str}"

    @staticmethod
    def format_timestamp(timestamp: Optional[int]) -> str:
        """格式化时间戳"""
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return "N/A"

    @staticmethod
    def calculate_change_amount(current_price: float, change_percent: Optional[float]) -> Optional[float]:
        """计算涨跌金额"""
        if change_percent is None:
            return None
        return current_price * (change_percent / 100)

    @staticmethod
    def get_data_freshness(last_update: Optional[float]) -> str:
        """获取数据新鲜度描述"""
        if not last_update:
            return "未知"

        age = time.time() - last_update
        if age < 30:
            return "刚刚更新"
        elif age < 60:
            return f"{int(age)}秒前"
        elif age < 300:
            return f"{int(age / 60)}分钟前"
        else:
            return "数据可能已过期"


# ==================== 应用状态管理 ====================
class AppState:
    """应用状态管理"""

    @staticmethod
    def initialize():
        """初始化session state"""
        defaults = {
            'btc_data': None,
            'last_update_time': None,
            'is_loading': False,
            'error_message': None,
            'auto_refresh_enabled': True,
            'refresh_interval': 30,
            'last_auto_refresh': None
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def update_data(new_data: Dict[str, Any]):
        """更新数据"""
        st.session_state.btc_data = new_data
        st.session_state.last_update_time = time.time()
        st.session_state.error_message = None

    @staticmethod
    def set_error(error_msg: str):
        """设置错误信息"""
        st.session_state.error_message = error_msg
        st.session_state.is_loading = False

    @staticmethod
    def should_auto_refresh() -> bool:
        """检查是否应该自动刷新"""
        if not st.session_state.auto_refresh_enabled:
            return False

        if not st.session_state.last_update_time:
            return True

        current_time = time.time()
        time_since_last_update = current_time - st.session_state.last_update_time

        return time_since_last_update >= st.session_state.refresh_interval


# ==================== UI组件 ====================
class UIComponents:
    """UI组件"""

    def __init__(self, data_processor: DataProcessor):
        self.dp = data_processor

    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.header("设置")

            # 自动刷新配置
            st.session_state.auto_refresh_enabled = st.checkbox(
                "启用自动刷新",
                value=st.session_state.auto_refresh_enabled
            )

            if st.session_state.auto_refresh_enabled:
                st.session_state.refresh_interval = st.slider(
                    "刷新间隔(秒)",
                    min_value=10,
                    max_value=300,
                    value=st.session_state.refresh_interval,
                    help="设置自动刷新的时间间隔"
                )

            st.markdown("---")
            st.markdown("### 数据源")
            st.markdown("数据来自 [CoinGecko API](https://www.coingecko.com/)")
            st.markdown("---")
            st.markdown("### 应用信息")
            st.markdown("""
            这是一个实时比特币价格追踪应用，显示：
            - 当前价格 (USD)
            - 24小时价格变化
            - 最后更新时间
            """)

    def render_header(self):
        """渲染页面头部"""
        st.title("₿ 比特币价格追踪器")
        st.markdown("---")

    def render_refresh_controls(self):
        """渲染刷新控制"""
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 刷新数据", type="primary", use_container_width=True):
                st.session_state.is_loading = True
                st.rerun()

        with col2:
            if st.session_state.last_update_time:
                freshness = self.dp.get_data_freshness(st.session_state.last_update_time)
                st.caption(f"数据状态: {freshness}")

    def render_loading_state(self):
        """渲染加载状态"""
        if st.session_state.is_loading:
            with st.spinner("正在获取最新数据..."):
                # 这里不阻塞，只是显示状态
                pass

    def render_error_state(self):
        """渲染错误状态"""
        if st.session_state.error_message:
            st.error(f"❌ {st.session_state.error_message}")

            # 如果有缓存数据，提示用户
            if st.session_state.btc_data:
                st.info("正在显示缓存数据，可能不是最新的")
            else:
                st.info("请检查网络连接后点击刷新按钮重试")

    def render_price_display(self, data: Dict[str, Any]):
        """渲染价格显示"""
        current_price = data['current_price']
        price_change = data['price_change_24h']
        change_amount = self.dp.calculate_change_amount(current_price, price_change)

        # 使用metric组件显示价格
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="当前价格",
                value=self.dp.format_price(current_price),
                delta=None
            )

        with col2:
            delta_value = f"${change_amount:+.2f}" if change_amount else None
            st.metric(
                label="24小时变化",
                value=self.dp.format_price(current_price),
                delta=delta_value
            )

        with col3:
            # 使用HTML自定义样式显示涨跌幅
            change_color = "green" if price_change > 0 else "red" if price_change < 0 else "gray"
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <div style="font-size: 0.9em; color: gray; margin-bottom: 5px;">24小时涨跌幅</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: {change_color};">
                        {self.dp.format_change(price_change)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # 价格变化趋势指示器
        self._render_trend_indicator(price_change)

        # 显示原始更新时间戳
        if data['last_updated']:
            st.caption(f"数据更新时间: {self.dp.format_timestamp(data['last_updated'])}")

    def _render_trend_indicator(self, price_change: float):
        """渲染趋势指示器"""
        st.markdown("---")
        st.subheader("价格趋势指示")

        # 简单的趋势指示器
        if price_change > 5:
            trend = "🚀 强势上涨"
            color = "green"
        elif price_change > 0:
            trend = "📈 温和上涨"
            color = "lightgreen"
        elif price_change < -5:
            trend = "⚠️ 大幅下跌"
            color = "red"
        elif price_change < 0:
            trend = "📉 小幅下跌"
            color = "lightcoral"
        else:
            trend = "➡️ 价格平稳"
            color = "gray"

        st.markdown(
            f'<div style="background-color: {color}20; padding: 15px; border-radius: 10px; border-left: 5px solid {color};">'
            f'<h4 style="margin: 0; color: {color};">{trend}</h4>'
            f'</div>',
            unsafe_allow_html=True
        )

    def render_empty_state(self):
        """渲染空状态"""
        st.info("👈 点击刷新按钮获取比特币实时价格")

        # 显示示例数据（仅用于布局展示）
        st.markdown("---")
        st.subheader("示例展示")

        example_col1, example_col2, example_col3 = st.columns(3)

        with example_col1:
            st.metric(
                label="当前价格",
                value="$--,--",
                delta=None
            )

        with example_col2:
            st.metric(
                label="24小时变化",
                value="$--,--",
                delta="+$--"
            )

        with example_col3:
            st.markdown(
                """
                <div style="text-align: center;">
                    <div style="font-size: 0.9em; color: gray; margin-bottom: 5px;">24小时涨跌幅</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: gray;">
                        +--.--%
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ==================== 主应用 ====================
class BitcoinPriceApp:
    """比特币价格应用主类"""

    def __init__(self):
        self.api_client = BitcoinAPIClient()
        self.data_processor = DataProcessor()
        self.ui = UIComponents(self.data_processor)
        AppState.initialize()

    def fetch_data_with_fallback(self):
        """获取数据，支持降级策略"""
        try:
            # 尝试获取新数据
            new_data = self.api_client.fetch_bitcoin_price()
            AppState.update_data(new_data)
            logger.info("成功更新比特币价格数据")

        except (APINotAvailableError, NetworkError, InvalidDataError) as e:
            # 对于已知错误，设置错误信息
            AppState.set_error(str(e))
            logger.warning(f"获取实时数据失败: {str(e)}")

            # 如果有缓存数据，继续使用
            if not st.session_state.btc_data:
                # 没有缓存数据时，设置默认值
                st.session_state.btc_data = {
                    'current_price': 0,
                    'price_change_24h': 0,
                    'last_updated': None
                }

        except Exception as e:
            # 未知错误
            error_msg = "系统错误，请稍后重试"
            AppState.set_error(error_msg)
            logger.error(f"未知错误: {str(e)}")

        finally:
            st.session_state.is_loading = False

    def handle_auto_refresh(self):
        """处理自动刷新逻辑"""
        if AppState.should_auto_refresh():
            logger.info("触发自动刷新")
            st.session_state.is_loading = True
            # 设置一个标记，避免重复触发
            st.session_state.last_update_time = time.time()
            self.fetch_data_with_fallback()
            st.rerun()

    def run(self):
        """运行应用"""
        # 初始化数据（如果为空）
        if st.session_state.btc_data is None and not st.session_state.is_loading:
            st.session_state.is_loading = True
            self.fetch_data_with_fallback()
            st.rerun()

        # 处理手动刷新
        if st.session_state.is_loading:
            self.fetch_data_with_fallback()
            st.rerun()

        # 渲染UI
        self.ui.render_header()
        self.ui.render_sidebar()
        self.ui.render_refresh_controls()
        self.ui.render_loading_state()
        self.ui.render_error_state()

        # 显示数据
        if st.session_state.btc_data:
            self.ui.render_price_display(st.session_state.btc_data)
        else:
            self.ui.render_empty_state()

        # 检查自动刷新
        self.handle_auto_refresh()


# ==================== 应用入口 ====================
def main():
    """主函数"""
    app = BitcoinPriceApp()
    app.run()


if __name__ == "__main__":
    main()