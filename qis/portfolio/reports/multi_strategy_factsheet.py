"""
factsheet for multi strategy report for cross sectional comparison of strategies
and generating sensitivities to parameters
see example in qis.examples.factheets.multi_strategy.py
"""
# packages
import matplotlib.pyplot as plt
from typing import Tuple

# qis
import qis
from qis import TimePeriod, PerfParams, PerfStat, BenchmarkReturnsQuantileRegimeSpecs

# portfolio
from qis.portfolio.multi_portfolio_data import MultiPortfolioData
from qis.portfolio.reports.config import PERF_PARAMS, REGIME_PARAMS


def generate_multi_portfolio_factsheet(multi_portfolio_data: MultiPortfolioData,
                                       time_period: TimePeriod = None,
                                       perf_params: PerfParams = PERF_PARAMS,
                                       regime_params: BenchmarkReturnsQuantileRegimeSpecs = REGIME_PARAMS,
                                       backtest_name: str = None,
                                       figsize: Tuple[float, float] = (8.3, 11.7),  # A4 for portrait
                                       **kwargs
                                       ):
    """
    for portfolio data with structurally different strategies
    """
    regime_benchmark = multi_portfolio_data.benchmark_prices.columns[0]
    benchmark_price = multi_portfolio_data.benchmark_prices[regime_benchmark]

    plot_kwargs = dict(fontsize=5,
                       linewidth=0.5,
                       digits_to_show=1, sharpe_digits=2,
                       weight='normal',
                       markersize=1,
                       framealpha=0.75)
    kwargs = qis.update_kwargs(kwargs, plot_kwargs)

    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(nrows=7, ncols=4, wspace=0.0, hspace=0.0)

    if backtest_name is not None:
        fig.suptitle(backtest_name, fontweight="bold", fontsize=8, color='blue')

    multi_portfolio_data.plot_nav(ax=fig.add_subplot(gs[0, :2]),
                                  time_period=time_period,
                                  benchmark=regime_benchmark,
                                  perf_params=perf_params,
                                  regime_params=regime_params,
                                  title='Cumulative performance',
                                  **kwargs)

    multi_portfolio_data.plot_drawdowns(ax=fig.add_subplot(gs[1, :2]),
                                        time_period=time_period,
                                        benchmark=regime_benchmark,
                                        regime_params=regime_params,
                                        title='Running Drawdowns',
                                        **kwargs)

    multi_portfolio_data.plot_rolling_time_under_water(ax=fig.add_subplot(gs[2, :2]),
                                                       time_period=time_period,
                                                       benchmark=regime_benchmark,
                                                       regime_params=regime_params,
                                                       title='Rolling time under water',
                                                       **kwargs)

    multi_portfolio_data.plot_exposures(ax=fig.add_subplot(gs[3, :2]),
                                        portfolio_idx=0,
                                        time_period=time_period,
                                        benchmark=regime_benchmark,
                                        regime_params=regime_params,
                                        **kwargs)

    multi_portfolio_data.plot_turnover(ax=fig.add_subplot(gs[4, :2]),
                                       time_period=time_period,
                                       benchmark=regime_benchmark,
                                       regime_params=regime_params,
                                       **kwargs)

    multi_portfolio_data.plot_costs(ax=fig.add_subplot(gs[5, :2]),
                                    time_period=time_period,
                                    benchmark=regime_benchmark,
                                    regime_params=regime_params,
                                    **kwargs)

    multi_portfolio_data.plot_factor_betas(ax=fig.add_subplot(gs[6, :2]),
                                           benchmark_prices=multi_portfolio_data.benchmark_prices,
                                           time_period=time_period,
                                           benchmark=regime_benchmark,
                                           regime_params=regime_params,
                                           **kwargs)

    multi_portfolio_data.plot_performance_bars(ax=fig.add_subplot(gs[0, 2]),
                                               perf_params=perf_params,
                                               perf_column=PerfStat.SHARPE,
                                               time_period=time_period,
                                               **qis.update_kwargs(kwargs, dict(fontsize=5)))

    multi_portfolio_data.plot_performance_bars(ax=fig.add_subplot(gs[0, 3]),
                                               perf_params=perf_params,
                                               perf_column=PerfStat.MAX_DD,
                                               time_period=time_period,
                                               **qis.update_kwargs(kwargs, dict(fontsize=5)))

    multi_portfolio_data.plot_periodic_returns(ax=fig.add_subplot(gs[1, 2:]),
                                               heatmap_freq='A',
                                               time_period=time_period,
                                               **qis.update_kwargs(kwargs, dict(date_format='%Y', fontsize=5)))

    multi_portfolio_data.plot_ra_perf_table(ax=fig.add_subplot(gs[2, 2:]),
                                            perf_params=perf_params,
                                            time_period=time_period,
                                            **qis.update_kwargs(kwargs, dict(fontsize=5)))

    multi_portfolio_data.plot_ra_perf_table(ax=fig.add_subplot(gs[3, 2:]),
                                            perf_params=perf_params,
                                            time_period=qis.get_time_period_shifted_by_years(time_period=time_period),
                                            **qis.update_kwargs(kwargs, dict(fontsize=5)))

    multi_portfolio_data.plot_regime_data(ax=fig.add_subplot(gs[4, 2:]),
                                          is_grouped=False,
                                          time_period=time_period,
                                          perf_params=perf_params,
                                          regime_params=regime_params,
                                          benchmark=regime_benchmark,
                                          **kwargs)

    multi_portfolio_data.plot_returns_scatter(ax=fig.add_subplot(gs[5, 2:]),
                                              time_period=time_period,
                                              benchmark=regime_benchmark,
                                              **kwargs)

    multi_portfolio_data.plot_corr_table(ax=fig.add_subplot(gs[6, 2:]),
                                         time_period=time_period,
                                         freq='W-WED',
                                         **qis.update_kwargs(kwargs, dict(fontsize=4)))

    return fig
