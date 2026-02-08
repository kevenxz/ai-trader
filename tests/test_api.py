# AlphaPulse API 测试用例

import pytest
import httpx
from datetime import datetime

# =============================================
# 配置
# =============================================

BASE_URL = "http://localhost:8000/api"
TEST_ORDER_ID = None  # 动态设置


# =============================================
# 订单管理测试
# =============================================

class TestOrderManagement:
    """订单管理接口测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        yield
        self.client.close()
    
    def test_get_orders_list(self):
        """测试获取订单列表"""
        response = self.client.get("/orders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_orders_with_filters(self):
        """测试带筛选条件的订单列表"""
        response = self.client.get("/orders", params={
            "symbol": "BTCUSDT",
            "status": "OPEN",
            "limit": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 检查所有返回的订单都符合筛选条件
        for order in data:
            assert order.get("symbol") == "BTCUSDT"
            assert order.get("status") == "OPEN"
    
    def test_get_orders_by_date_range(self):
        """测试日期范围筛选"""
        response = self.client.get("/orders", params={
            "start_date": "2026-01-01",
            "end_date": "2026-02-01"
        })
        assert response.status_code == 200
    
    def test_create_order(self):
        """测试创建订单"""
        global TEST_ORDER_ID
        order_data = {
            "symbol": "BTCUSDT",
            "interval": "4h",
            "recommendation": "BUY",
            "risk_level": "MEDIUM",
            "entry_price": 95000.0,
            "stop_loss": 93000.0,
            "target_t1": 97000.0,
            "target_t2": 99000.0,
            "target_t3": 101000.0,
            "leverage": 10,
            "quantity": 0.01,
            "open_amount": 950.0,
            "analysis_summary": "测试订单"
        }
        response = self.client.post("/orders", json=order_data)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["recommendation"] == "BUY"
        assert data["id"] is not None
        TEST_ORDER_ID = data["id"]
    
    def test_create_order_missing_required_fields(self):
        """测试创建订单缺少必填字段"""
        order_data = {
            "symbol": "BTCUSDT"
            # 缺少 entry_price, stop_loss 等必填字段
        }
        response = self.client.post("/orders", json=order_data)
        assert response.status_code == 422  # Validation Error
    
    def test_get_order_detail(self):
        """测试获取订单详情"""
        if TEST_ORDER_ID is None:
            pytest.skip("需要先创建订单")
        
        response = self.client.get(f"/orders/{TEST_ORDER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_ORDER_ID
    
    def test_get_order_not_found(self):
        """测试获取不存在的订单"""
        response = self.client.get("/orders/99999")
        assert response.status_code == 404


# =============================================
# 盈亏计算测试
# =============================================

class TestProfitCalculation:
    """盈亏计算接口测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        yield
        self.client.close()
    
    def test_calculate_order_profit(self):
        """测试计算单个订单盈亏"""
        if TEST_ORDER_ID is None:
            pytest.skip("需要先有开放订单")
        
        response = self.client.post(f"/orders/{TEST_ORDER_ID}/calculate-profit")
        assert response.status_code in [200, 400]  # 400 if order not open
        if response.status_code == 200:
            data = response.json()
            assert "current_price" in data
            assert "profit_percentage" in data
            assert "is_stop_loss_triggered" in data
    
    def test_calculate_profit_not_found(self):
        """测试计算不存在订单的盈亏"""
        response = self.client.post("/orders/99999/calculate-profit")
        assert response.status_code == 404
    
    def test_calculate_all_profits(self):
        """测试批量计算所有订单盈亏"""
        response = self.client.post("/orders/calculate-all-profits")
        assert response.status_code == 200
        data = response.json()
        assert "processed" in data
        assert "results" in data
    
    def test_get_order_profit_history(self):
        """测试获取订单盈亏历史"""
        if TEST_ORDER_ID is None:
            pytest.skip("需要先有订单")
        
        response = self.client.get(f"/orders/{TEST_ORDER_ID}/profit-history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# =============================================
# 仪表盘测试
# =============================================

class TestDashboard:
    """仪表盘接口测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        yield
        self.client.close()
    
    def test_get_dashboard(self):
        """测试获取仪表盘数据"""
        response = self.client.get("/orders/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_profit_percentage" in data
        assert "total_orders" in data
        assert "win_rate" in data
        assert "symbol_stats" in data
    
    def test_get_daily_profit(self):
        """测试获取每日盈亏"""
        response = self.client.get("/orders/dashboard/daily-profit", params={"days": 30})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "date" in data[0]
            assert "total_profit" in data[0]
    
    def test_get_interval_stats(self):
        """测试获取周期统计"""
        response = self.client.get("/orders/dashboard/interval-stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_profit_curve(self):
        """测试获取收益曲线"""
        response = self.client.get("/orders/dashboard/profit-curve", params={"days": 90})
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "days" in data
        assert "data_points" in data
        assert "total_profit_percentage" in data
        assert "total_profit_amount" in data
        assert "curve" in data
        assert isinstance(data["curve"], list)
        
        # 验证曲线数据结构
        if len(data["curve"]) > 0:
            point = data["curve"][0]
            assert "date" in point
            assert "daily_profit" in point
            assert "daily_profit_amount" in point
            assert "cumulative_profit" in point
            assert "cumulative_profit_amount" in point
            assert "order_count" in point
    
    def test_get_profit_curve_with_symbol_filter(self):
        """测试按币种筛选收益曲线"""
        response = self.client.get("/orders/dashboard/profit-curve", params={
            "days": 30,
            "symbol": "BTCUSDT"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
    
    def test_get_available_symbols(self):
        """测试获取可用币种列表"""
        response = self.client.get("/orders/dashboard/available-symbols")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # 验证数据结构
        if len(data) > 0:
            symbol_item = data[0]
            assert "symbol" in symbol_item
            assert "order_count" in symbol_item


# =============================================
# 实时追踪测试
# =============================================

class TestRealtimeTracking:
    """实时追踪接口测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        yield
        self.client.close()
    
    def test_get_realtime_config(self):
        """测试获取实时追踪配置"""
        if TEST_ORDER_ID is None:
            pytest.skip("需要先有订单")
        
        response = self.client.get(f"/realtime/orders/{TEST_ORDER_ID}")
        assert response.status_code == 200
    
    def test_enable_realtime_tracking(self):
        """测试启用实时追踪"""
        if TEST_ORDER_ID is None:
            pytest.skip("需要先有订单")
        
        response = self.client.post(f"/realtime/orders/{TEST_ORDER_ID}/enable")
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_enabled") == True
    
    def test_disable_realtime_tracking(self):
        """测试禁用实时追踪"""
        if TEST_ORDER_ID is None:
            pytest.skip("需要先有订单")
        
        response = self.client.post(f"/realtime/orders/{TEST_ORDER_ID}/disable")
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_enabled") == False
    
    def test_update_tracking_interval(self):
        """测试更新追踪周期"""
        if TEST_ORDER_ID is None:
            pytest.skip("需要先有订单")
        
        response = self.client.put(
            f"/realtime/orders/{TEST_ORDER_ID}",
            json={"tracking_interval": "1h"}
        )
        assert response.status_code == 200


# =============================================
# 定时任务测试
# =============================================

class TestScheduler:
    """定时任务接口测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        yield
        self.client.close()
    
    def test_get_scheduler_status(self):
        """测试获取调度器状态"""
        response = self.client.get("/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
    
    def test_get_scheduler_jobs(self):
        """测试获取任务列表"""
        response = self.client.get("/scheduler/jobs")
        assert response.status_code == 200
        jobs = response.json()
        assert isinstance(jobs, list)
        # 验证返回字段结构
        if len(jobs) > 0:
            job = jobs[0]
            assert "job_id" in job
            assert "symbol" in job
            assert "interval" in job
            assert "status" in job
    
    def test_start_scheduler(self):
        """测试启动调度器"""
        response = self.client.post("/scheduler/start")
        assert response.status_code == 200
    
    def test_stop_scheduler(self):
        """测试停止调度器"""
        response = self.client.post("/scheduler/stop")
        assert response.status_code == 200
    
    def test_add_scheduler_job_with_trader_config(self):
        """测试添加定时任务（带trader配置）"""
        job_data = {
            "symbol": "BTCUSDT",
            "interval": "15m",
            "schedule_type": "m",
            "schedule_value": 15,
            "service": "guiji",
            "klines_count": 100,
            "temperature": 0.7,
            "enable_thinking": False,
            "is_trader": True
        }
        response = self.client.post("/scheduler/jobs", json=job_data)
        assert response.status_code in [200, 400]  # 400 if job exists
        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == "BTCUSDT"
            assert data["service"] == "guiji"
            assert data["klines_count"] == 100
    
    def test_pause_and_resume_job(self):
        """测试暂停和恢复单个任务"""
        # 先添加一个任务
        job_data = {
            "symbol": "ETHUSDT",
            "interval": "1h",
            "schedule_type": "m",
            "schedule_value": 30
        }
        add_response = self.client.post("/scheduler/jobs", json=job_data)
        
        if add_response.status_code == 200:
            job_id = add_response.json()["job_id"]
            
            # 测试暂停
            pause_response = self.client.post(f"/scheduler/jobs/{job_id}/pause")
            assert pause_response.status_code == 200
            assert pause_response.json()["status"] == "paused"
            
            # 测试恢复
            resume_response = self.client.post(f"/scheduler/jobs/{job_id}/resume")
            assert resume_response.status_code == 200
            assert resume_response.json()["status"] == "active"
            
            # 清理：删除任务
            self.client.delete(f"/scheduler/jobs/{job_id}")
    
    def test_pause_nonexistent_job(self):
        """测试暂停不存在的任务"""
        response = self.client.post("/scheduler/jobs/nonexistent_job_id/pause")
        assert response.status_code == 404
    
    def test_delete_scheduler_job(self):
        """测试删除定时任务"""
        # 先添加一个任务
        job_data = {
            "symbol": "SOLUSDT",
            "interval": "4h",
            "schedule_type": "h",
            "schedule_value": 1
        }
        add_response = self.client.post("/scheduler/jobs", json=job_data)
        
        if add_response.status_code == 200:
            job_id = add_response.json()["job_id"]
            # 删除任务
            del_response = self.client.delete(f"/scheduler/jobs/{job_id}")
            assert del_response.status_code == 200


# =============================================
# 盈亏追踪器测试
# =============================================

class TestProfitTracker:
    """盈亏追踪器接口测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        yield
        self.client.close()
    
    def test_get_tracker_status(self):
        """测试获取追踪器状态"""
        response = self.client.get("/orders/profit-tracker/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
    
    def test_start_tracker(self):
        """测试启动追踪器"""
        response = self.client.post("/orders/profit-tracker/start")
        assert response.status_code == 200
    
    def test_stop_tracker(self):
        """测试停止追踪器"""
        response = self.client.post("/orders/profit-tracker/stop")
        assert response.status_code == 200


# =============================================
# 订单关闭测试
# =============================================

class TestOrderClose:
    """订单关闭测试 (放在最后执行)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        yield
        self.client.close()
    
    def test_close_order(self):
        """测试关闭订单"""
        if TEST_ORDER_ID is None:
            pytest.skip("需要先创建订单")
        
        response = self.client.delete(f"/orders/{TEST_ORDER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] != "OPEN"
    
    def test_close_order_with_price(self):
        """测试指定价格关闭订单"""
        # 需要先创建一个新订单
        order_data = {
            "symbol": "ETHUSDT",
            "recommendation": "BUY",
            "entry_price": 3500.0,
            "stop_loss": 3400.0
        }
        create_response = self.client.post("/orders", json=order_data)
        if create_response.status_code != 200:
            pytest.skip("无法创建测试订单")
        
        new_order_id = create_response.json()["id"]
        
        response = self.client.delete(
            f"/orders/{new_order_id}",
            params={"closed_price": 3550.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["closed_price"] == 3550.0


# =============================================
# 运行测试
# =============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
