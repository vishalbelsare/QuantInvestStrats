"""
generate strategy factsheet report with comparision to benchmark strategy using MultiPortfolioData object
for test implementation see qis.examples.portfolio_factsheet
"""
import numpy as np
# packages
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Dict
import qis as qis
from qis import TimePeriod, PerfParams, BenchmarkReturnsQuantileRegimeSpecs

# portfolio
from qis.portfolio.portfolio_data import AttributionMetric
from qis.portfolio.multi_portfolio_data import MultiPortfolioData
from qis.portfolio.reports.strategy_factsheet import generate_strategy_factsheet
from qis.portfolio.reports.config import PERF_PARAMS, REGIME_PARAMS


def generate_strategy_benchmark_factsheet_plt(multi_portfolio_data: MultiPortfolioData,
                                              strategy_idx: int = 0,  # strategy is multi_portfolio_data[strategy_idx]
                                              benchmark_idx: int = 1,  # benchmark is multi_portfolio_data[benchmark_idx]
                                              time_period: TimePeriod = None,
                                              perf_params: PerfParams = PERF_PARAMS,
                                              regime_params: BenchmarkReturnsQuantileRegimeSpecs = REGIME_PARAMS,
                                              backtest_name: str = None,
                                              add_benchmarks_to_navs: bool = False,
                                              add_brinson_attribution: bool = True,
                                              add_exposures_pnl_attribution: bool = False,
                                              add_strategy_factsheet: bool = False,
                                              add_grouped_exposures: bool = False,  # for strategy factsheet
                                              add_grouped_cum_pnl: bool = False,  # for strategy factsheet
                                              add_tracking_error_table: bool = False,
                                              add_exposures_comp: bool = False,
                                              is_grouped: Optional[bool] = None,
                                              figsize: Tuple[float, float] = (8.3, 11.7),  # A4 for portrait
                                              fontsize: int = 4,
                                              **kwargs
                                              ) -> List[plt.Figure]:
    """
    report designed for 1 strategy and 1 benchmark report using matplotlib figure
    multi_portfolio_data = [stragegy portfolio, benchmark strategy portfolio]
    1 page: generate the stragegy portfolio factsheet
    2 page: generate the comparision to benchmark
    """
    if len(multi_portfolio_data.portfolio_datas) == 1:
        raise ValueError(f"must be at least two strategies")

    if is_grouped is None:
        if len(multi_portfolio_data.portfolio_datas[0].get_weights().columns) >= 10:  # otherwise tables look too bad
            is_grouped = True
        else:
            is_grouped = False

    # set reporting time period here
    if time_period is None:
        time_period = qis.get_time_period(multi_portfolio_data.portfolio_datas[0].get_portfolio_nav())

    # set report specific kqargs
    plot_kwargs = dict(fontsize=fontsize,
                       linewidth=0.5,
                       digits_to_show=1, sharpe_digits=2,
                       weight='normal',
                       markersize=1,
                       framealpha=0.75,
                       time_period=time_period)
    kwargs = qis.update_kwargs(kwargs, plot_kwargs)

    figs = []
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    figs.append(fig)
    gs = fig.add_gridspec(nrows=14, ncols=4, wspace=0.0, hspace=0.0)

    if backtest_name is not None:
        fig.suptitle(backtest_name, fontweight="bold", fontsize=8, color='blue')

    regime_benchmark = multi_portfolio_data.benchmark_prices.columns[0]
    benchmark_price = multi_portfolio_data.benchmark_prices[regime_benchmark]

    multi_portfolio_data.plot_nav(ax=fig.add_subplot(gs[:2, :2]),
                                  add_benchmarks_to_navs=add_benchmarks_to_navs,
                                  regime_benchmark=regime_benchmark,
                                  perf_params=perf_params,
                                  regime_params=regime_params,
                                  title=f"Cumulative performance with background colors using bear/normal/bull regimes of {regime_benchmark} {regime_params.freq}-returns",
                                  **kwargs)

    multi_portfolio_data.plot_drawdowns(ax=fig.add_subplot(gs[2:4, :2]),
                                        add_benchmarks_to_navs=add_benchmarks_to_navs,
                                        regime_benchmark=regime_benchmark,
                                        regime_params=regime_params,
                                        title='Running Drawdowns',
                                        **kwargs)

    multi_portfolio_data.plot_rolling_time_under_water(ax=fig.add_subplot(gs[4:6, :2]),
                                                       add_benchmarks_to_navs=add_benchmarks_to_navs,
                                                       regime_benchmark=regime_benchmark,
                                                       regime_params=regime_params,
                                                       title='Rolling time under water',
                                                       **kwargs)

    multi_portfolio_data.plot_rolling_perf(ax=fig.add_subplot(gs[6:8, :2]),
                                           add_benchmarks_to_navs=add_benchmarks_to_navs,
                                           regime_benchmark=regime_benchmark,
                                           regime_params=regime_params,
                                           **kwargs)

    multi_portfolio_data.plot_exposures(ax=fig.add_subplot(gs[8:10, :2]),
                                        benchmark=regime_benchmark,
                                        regime_params=regime_params,
                                        **kwargs)

    multi_portfolio_data.plot_turnover(ax=fig.add_subplot(gs[10:12, :2]),
                                       benchmark=regime_benchmark,
                                       regime_params=regime_params,
                                       **kwargs)

    multi_portfolio_data.plot_costs(ax=fig.add_subplot(gs[12:14, :2]),
                                    benchmark=regime_benchmark,
                                    regime_params=regime_params,
                                    **kwargs)

    multi_portfolio_data.plot_ac_ra_perf_table(ax=fig.add_subplot(gs[0:2, 2:]),
                                               benchmark_price=benchmark_price,
                                               add_benchmarks_to_navs=add_benchmarks_to_navs,
                                               perf_params=perf_params,
                                               is_grouped=is_grouped,
                                               **qis.update_kwargs(kwargs, dict(fontsize=fontsize)))

    time_period1 = qis.get_time_period_shifted_by_years(time_period=time_period, n_years=1)
    # change regression to weekly
    if pd.infer_freq(benchmark_price.index) in ['B', 'D']:
        local_kwargs = qis.update_kwargs(kwargs, dict(time_period=time_period1, alpha_an_factor=52, freq_reg='W-WED', fontsize=fontsize))
    else:
        local_kwargs = qis.update_kwargs(kwargs, dict(time_period=time_period1, fontsize=fontsize))

    multi_portfolio_data.plot_ac_ra_perf_table(ax=fig.add_subplot(gs[2:4, 2:]),
                                               benchmark_price=benchmark_price,
                                               add_benchmarks_to_navs=add_benchmarks_to_navs,
                                               perf_params=perf_params,
                                               is_grouped=is_grouped,
                                               **local_kwargs)

    # periodic returns
    local_kwargs = qis.update_kwargs(kwargs=kwargs,
                                     new_kwargs=dict(fontsize=fontsize, square=False, x_rotation=90, transpose=False))
    if add_benchmarks_to_navs:
        benchmark_prices = multi_portfolio_data.benchmark_prices
    else:
        benchmark_prices = None
    multi_portfolio_data.portfolio_datas[0].plot_periodic_returns(is_grouped=is_grouped,
                                                                  benchmark_prices=benchmark_prices,
                                                                  ax=fig.add_subplot(gs[4:6, 2]),
                                                                  **local_kwargs)

    multi_portfolio_data.portfolio_datas[1].plot_periodic_returns(is_grouped=is_grouped,
                                                                  benchmark_prices=benchmark_prices,
                                                                  ax=fig.add_subplot(gs[4:6, 3]),
                                                                  **local_kwargs)

    # gross comparision
    post_title = f"Sharpe ratio split to {str(benchmark_price.name)} Bear/Normal/Bull {regime_params.freq}-freq regimes"
    """
    multi_portfolio_data.portfolio_datas[0].plot_regime_data(benchmark_price=benchmark_price,
                                                             is_grouped=False,
                                                             title=f"{multi_portfolio_data.portfolio_datas[0].nav.name} {post_title}",
                                                             perf_params=perf_params,
                                                             regime_params=regime_params,
                                                             ax=fig.add_subplot(gs[6:8, 2]),
                                                             **qis.update_kwargs(kwargs, dict(fontsize=fontsize, x_rotation=90)))
    """
    multi_portfolio_data.plot_regime_data(benchmark=str(benchmark_price.name),
                                          add_benchmarks_to_navs=add_benchmarks_to_navs,
                                          is_grouped=False,
                                          title=f"{post_title}",
                                          perf_params=perf_params,
                                          regime_params=regime_params,
                                          ax=fig.add_subplot(gs[6:8, 2]),
                                          **qis.update_kwargs(kwargs, dict(fontsize=fontsize, x_rotation=90)))

    # strategy by asset class
    multi_portfolio_data.portfolio_datas[0].plot_regime_data(benchmark_price=benchmark_price,
                                                             add_benchmarks_to_navs=add_benchmarks_to_navs,
                                                             is_grouped=False,
                                                             title=f"{multi_portfolio_data.portfolio_datas[0].nav.name} {post_title}",
                                                             perf_params=perf_params,
                                                             regime_params=regime_params,
                                                             ax=fig.add_subplot(gs[6:8, 3]),
                                                             **qis.update_kwargs(kwargs, dict(fontsize=fontsize, x_rotation=90)))

    # vol regimes
    """
    multi_portfolio_data.portfolio_datas[0].plot_vol_regimes(ax=fig.add_subplot(gs[8:10, 2]),
                                                             benchmark_price=benchmark_price,
                                                             perf_params=perf_params,
                                                             freq=regime_params.freq,
                                                             **qis.update_kwargs(kwargs, dict(fontsize=fontsize, x_rotation=90)))
    multi_portfolio_data.portfolio_datas[1].plot_vol_regimes(ax=fig.add_subplot(gs[8:10, 3]),
                                                             benchmark_price=benchmark_price,
                                                             freq=perf_params.freq,
                                                             regime_params=regime_params,
                                                             **qis.update_kwargs(kwargs, dict(fontsize=fontsize, x_rotation=90)))
    """
    multi_portfolio_data.plot_instrument_pnl_diff(ax=fig.add_subplot(gs[8:10, 2:]),
                                                  benchmark=regime_benchmark,
                                                  regime_params=regime_params,
                                                  **kwargs)

    # plot beta to the regime_benchmark
    multi_portfolio_data.plot_factor_betas(axs=[fig.add_subplot(gs[10:12, 2:])],
                                           benchmark_prices=multi_portfolio_data.benchmark_prices[regime_benchmark].to_frame(),
                                           regime_benchmark=regime_benchmark,
                                           regime_params=regime_params,
                                           **kwargs)
    with sns.axes_style('whitegrid'):
        multi_portfolio_data.plot_returns_scatter(ax=fig.add_subplot(gs[12:, 2:]),
                                                  benchmark=regime_benchmark,
                                                  **qis.update_kwargs(kwargs, dict(freq=perf_params.freq_reg)))

    if add_brinson_attribution:
        with sns.axes_style("darkgrid"):
            fig1 = plt.figure(figsize=figsize, constrained_layout=True)
            fig1.suptitle(f'{backtest_name} Brinson performance attribution report', fontweight="bold", fontsize=8, color='blue')
            figs.append(fig1)
            gs = fig1.add_gridspec(nrows=3, ncols=2, wspace=0.0, hspace=0.0)
            axs = [fig1.add_subplot(gs[0, 0]), fig1.add_subplot(gs[0, 1]),
                   fig1.add_subplot(gs[1, 0]), fig1.add_subplot(gs[1, 1]),
                   fig1.add_subplot(gs[2, 1])]
            multi_portfolio_data.plot_brinson_attribution(strategy_idx=strategy_idx,
                                                          benchmark_idx=benchmark_idx,
                                                          freq=None,
                                                          axs=axs,
                                                          total_column='Total Sum',
                                                          is_exclude_interaction_term=True,
                                                          **kwargs)
        # add exposure diff
        multi_portfolio_data.plot_exposures_diff(ax=fig1.add_subplot(gs[2, 0]),
                                                 benchmark=regime_benchmark,
                                                 regime_params=regime_params,
                                                 **kwargs)

    if add_tracking_error_table:
        tre_table = multi_portfolio_data.compute_tracking_error_table(strategy_idx=strategy_idx,
                                                                      benchmark_idx=benchmark_idx,
                                                                      **kwargs)
        fig1, ax = plt.subplots(1, 1, figsize=qis.get_df_table_size(df=tre_table), constrained_layout=True)
        fig1.suptitle(f'{backtest_name} Tracking error table', fontweight="bold", fontsize=8, color='blue')
        figs.append(fig1)
        qis.plot_df_table(df=tre_table,
                          first_row_height=0.075,
                          var_format='{:.2%}',
                          rotation_for_columns_headers=90,
                          heatmap_columns=[x+1 for x in np.arange(len(tre_table.columns))],
                          ax=ax,
                          cmap='Blues',
                          **kwargs)

    if add_exposures_comp:
        strategy_name = multi_portfolio_data.portfolio_datas[strategy_idx].ticker
        benchmark_name = multi_portfolio_data.portfolio_datas[benchmark_idx].ticker
        strategy_weights, benchmark_weights = multi_portfolio_data.get_aligned_weights(strategy_idx=strategy_idx,
                                                                                       benchmark_idx=benchmark_idx,
                                                                                       is_grouped=is_grouped,
                                                                                       **kwargs)

        strategy_turnover, benchmark_turnover = multi_portfolio_data.get_aligned_turnover(strategy_idx=strategy_idx,
                                                                                          benchmark_idx=benchmark_idx,
                                                                                          is_grouped=is_grouped,
                                                                                          **kwargs)
        for inst in strategy_weights.columns:
            df1 = pd.concat([strategy_weights[inst].rename(strategy_name),
                            benchmark_weights[inst].rename(benchmark_name)], axis=1)
            df2 = pd.concat([strategy_turnover[inst].rename(strategy_name),
                            benchmark_turnover[inst].rename(benchmark_name)], axis=1)
            with sns.axes_style("darkgrid"):
                fig1, axs = plt.subplots(2, 1, figsize=figsize, constrained_layout=True)
                fig1.suptitle(f'{inst} Exposures and Turnover', fontweight="bold", fontsize=8, color='blue')
                figs.append(fig1)
                qis.plot_time_series(df=df1, title='Exposures',
                                     legend_stats=qis.LegendStats.AVG_MIN_MAX_LAST,
                                     var_format='{:,.2%}',
                                     ax=axs[0], **kwargs)
                qis.plot_time_series(df=df2, title='Turnover',
                                     legend_stats=qis.LegendStats.AVG_MIN_MAX_LAST,
                                     var_format='{:,.2%}',
                                     ax=axs[1], **kwargs)

            plt.close('all')

    if add_exposures_pnl_attribution:
        strategy_name = multi_portfolio_data.portfolio_datas[strategy_idx].ticker
        benchmark_name = multi_portfolio_data.portfolio_datas[benchmark_idx].ticker
        strategy_grouped_exposures_agg, strategy_grouped_exposures_by_inst = \
            multi_portfolio_data.portfolio_datas[strategy_idx].get_grouped_long_short_exposures(time_period=time_period)

        benchmark_grouped_exposures_agg, benchmark_grouped_exposures_by_inst = \
            multi_portfolio_data.portfolio_datas[benchmark_idx].get_grouped_long_short_exposures(time_period=time_period)

        strategy_grouped_pnls_agg, strategy_grouped_pnls_by_inst \
            = multi_portfolio_data.portfolio_datas[strategy_idx].get_grouped_cum_pnls(time_period=time_period)

        benchmark_grouped_pnls_agg, strategy_grouped_pnls_by_inst \
            = multi_portfolio_data.portfolio_datas[benchmark_idx].get_grouped_cum_pnls(time_period=time_period)

        nrows = len(strategy_grouped_exposures_agg.keys())
        fig2 = plt.figure(figsize=figsize, constrained_layout=True)
        figs.append(fig2)
        fig2.suptitle(f"{backtest_name}: Strategy vs Benchmark exposures by groups for period {time_period.to_str()}",
                     fontweight="bold", fontsize=8, color='blue')
        gs = fig2.add_gridspec(nrows=nrows, ncols=2, wspace=0.0, hspace=0.0)
        local_kwargs = qis.update_kwargs(kwargs=kwargs, new_kwargs=dict(framealpha=0.9))
        for idx, (group, exposures_agg) in enumerate(strategy_grouped_exposures_agg.items()):
            df1 = pd.concat([strategy_grouped_exposures_agg[group]['Total'].rename(strategy_name),
                             benchmark_grouped_exposures_agg[group]['Total'].rename(benchmark_name)],
                            axis=1)
            df2 = pd.concat([strategy_grouped_pnls_agg[group]['Total'].rename(strategy_name),
                             benchmark_grouped_pnls_agg[group]['Total'].rename(benchmark_name)],
                            axis=1)

            datas = {f"{group} aggregated net exposures": df1,
                     f"{group} cumulative P&L attribution": df2}
            for idx_, (key, df) in enumerate(datas.items()):
                ax = fig2.add_subplot(gs[idx, idx_])
                qis.plot_time_series(df=df,
                                     var_format='{:,.0%}',
                                     legend_stats=qis.LegendStats.AVG_MIN_MAX_LAST,
                                     title=f"{key}",
                                     ax=ax,
                                     **local_kwargs)
                multi_portfolio_data.add_regime_shadows(ax=ax, regime_benchmark=regime_benchmark, index=df.index, regime_params=regime_params)
                qis.set_spines(ax=ax, bottom_spine=False, left_spine=False)

    if add_strategy_factsheet:
        for portfolio_data in multi_portfolio_data.portfolio_datas:
            figs.append(generate_strategy_factsheet(portfolio_data=portfolio_data,
                                                    benchmark_prices=multi_portfolio_data.benchmark_prices,
                                                    perf_params=perf_params,
                                                    regime_params=regime_params,
                                                    add_grouped_exposures=add_grouped_exposures,
                                                    add_grouped_cum_pnl=add_grouped_cum_pnl,
                                                    is_grouped=is_grouped,
                                                    **kwargs  # time period will be in kwargs
                                                    ))
        figs = qis.to_flat_list(figs)
    return figs


def generate_strategy_benchmark_active_perf_plt(multi_portfolio_data: MultiPortfolioData,
                                                strategy_idx: int = 0,  # strategy is multi_portfolio_data[strategy_idx]
                                                benchmark_idx: int = 1, # benchmark is multi_portfolio_data[benchmark_idx]
                                                time_period: TimePeriod = None,
                                                perf_params: PerfParams = PERF_PARAMS,
                                                regime_params: BenchmarkReturnsQuantileRegimeSpecs = REGIME_PARAMS,
                                                backtest_name: str = None,
                                                weight_freq: Optional[str] = 'ME',
                                                add_strategy_factsheet: bool = False,
                                                add_grouped_exposures: bool = False,  # for strategy factsheet
                                                add_grouped_cum_pnl: bool = False,  # for strategy factsheet
                                                figsize: Tuple[float, float] = (8.3, 11.7),  # A4 for portrait
                                                is_long_only: bool = False,
                                                fontsize: int = 8,
                                                **kwargs
                                                ) -> List[plt.Figure]:
    """
    display 2*2 plot with nav and Brinson attribution
    """
    if len(multi_portfolio_data.portfolio_datas) == 1:
        raise ValueError(f"must be at least two strategies")

    # set report specific kqargs
    plot_kwargs = dict(fontsize=fontsize,
                       linewidth=1.0,
                       digits_to_show=1, sharpe_digits=2,
                       weight='normal',
                       markersize=1,
                       framealpha=0.75,
                       time_period=time_period,
                       perf_stats_labels=qis.PerfStatsLabels.DETAILED_WITH_DD.value)
    kwargs = qis.update_kwargs(kwargs, plot_kwargs)

    figs = []
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    figs.append(fig)
    gs = fig.add_gridspec(nrows=3, ncols=2, wspace=0.0, hspace=0.0)

    if backtest_name is not None:
        fig.suptitle(backtest_name, fontweight="bold", fontsize=8, color='blue')

    regime_benchmark = multi_portfolio_data.benchmark_prices.columns[0]
    benchmark_price = multi_portfolio_data.benchmark_prices[regime_benchmark]

    multi_portfolio_data.plot_nav(ax=fig.add_subplot(gs[0, 0]),
                                  regime_benchmark=regime_benchmark,
                                  perf_params=perf_params,
                                  regime_params=regime_params,
                                  title='Cumulative performance',
                                  **kwargs)

    totals_table, active_total, grouped_allocation_return, grouped_selection_return, grouped_interaction_return = \
        multi_portfolio_data.compute_brinson_attribution(strategy_idx=strategy_idx,
                                                         benchmark_idx=benchmark_idx,
                                                         freq=None,
                                                         time_period=time_period,
                                                         is_exclude_interaction_term=True)

    datas = {'Active total return (Brinson attribution)': (active_total.cumsum(0), fig.add_subplot(gs[0, 1])),
             'Asset class allocation return': (grouped_allocation_return.cumsum(0), fig.add_subplot(gs[1, 1])),
             'Instrument selection return': (grouped_selection_return.cumsum(0), fig.add_subplot(gs[2, 1]))}
    for key, (df, ax) in datas.items():
        legend_labels = [column + ', sum=' + '{:.1%}'.format(df[column].iloc[-1]) for column in df.columns]
        qis.plot_time_series(df=df,
                             title=key,
                             var_format='{:.1%}',
                             legend_labels=legend_labels,
                             ax=ax,
                             **kwargs)

        if regime_benchmark is not None:
            multi_portfolio_data.add_regime_shadows(ax=ax, regime_benchmark=regime_benchmark, index=df.index,
                                                    regime_params=regime_params)

    # weights box plot
    # make horizontal is too many instruments
    if len(multi_portfolio_data.portfolio_datas[0].prices.columns) > 9:
        local_kwargs = qis.update_kwargs(kwargs, dict(x_rotation=90, add_hue_to_legend_title=False))
    else:
        local_kwargs = qis.update_kwargs(kwargs, dict(add_hue_to_legend_title=False))
    ax = fig.add_subplot(gs[1, 0])
    multi_portfolio_data.plot_weights_boxplot(strategy_idx=strategy_idx,
                                              benchmark_idx=benchmark_idx,
                                              freq=weight_freq,
                                              is_grouped=True,
                                              title=f"Boxplot of weights by groups at {weight_freq}-freq",
                                              ax=ax,
                                              **local_kwargs)
    if is_long_only:
        qis.set_y_limits(ax=ax, y_limits=(0, None))
    ax = fig.add_subplot(gs[2, 0])
    multi_portfolio_data.plot_weights_boxplot(strategy_idx=strategy_idx,
                                              benchmark_idx=benchmark_idx,
                                              freq=weight_freq,
                                              is_grouped=False,
                                              title=f"Boxplot of weights by instruments at {weight_freq}-freq",
                                              ax=ax,
                                              **local_kwargs)
    if is_long_only:
        qis.set_y_limits(ax=ax, y_limits=(0, None))

    if add_strategy_factsheet:
        for portfolio_data in multi_portfolio_data.portfolio_datas:
            figs.append(generate_strategy_factsheet(portfolio_data=portfolio_data,
                                                    benchmark_prices=multi_portfolio_data.benchmark_prices,
                                                    perf_params=perf_params,
                                                    regime_params=regime_params,
                                                    add_grouped_exposures=add_grouped_exposures,
                                                    add_grouped_cum_pnl=add_grouped_cum_pnl,
                                                    **kwargs  # time period will be in kwargs
                                                    ))
        figs = qis.to_flat_list(figs)
    return figs


def generate_performance_attribution_report(multi_portfolio_data: MultiPortfolioData,
                                            time_period: TimePeriod = None,
                                            figsize: Tuple[float, float] = (8.3, 11.7),  # A4 for portrait
                                            **kwargs
                                            ) -> List[plt.Figure]:
    figs = []
    with sns.axes_style('darkgrid'):
        fig = plt.figure(figsize=figsize, constrained_layout=True)
        figs.append(fig)
        gs = fig.add_gridspec(nrows=3, ncols=2, wspace=0.0, hspace=0.0)

        multi_portfolio_data.plot_nav(ax=fig.add_subplot(gs[0, :]),
                                      time_period=time_period,
                                      **kwargs)

        multi_portfolio_data.plot_performance_attribution(portfolio_ids=[0],
                                                          time_period=time_period,
                                                          attribution_metric=AttributionMetric.PNL,
                                                          ax=fig.add_subplot(gs[1, :]),
                                                          **kwargs)

        multi_portfolio_data.plot_performance_attribution(portfolio_ids=[1],
                                                          time_period=time_period,
                                                          attribution_metric=AttributionMetric.PNL,
                                                          ax=fig.add_subplot(gs[2, :]),
                                                          **kwargs)

        fig, ax = plt.subplots(1, 1, figsize=figsize)
        figs.append(fig)
        multi_portfolio_data.plot_performance_periodic_table(portfolio_ids=[0],
                                                             time_period=time_period,
                                                             attribution_metric=AttributionMetric.INST_PNL,
                                                             freq='ME',
                                                             ax=ax,
                                                             **kwargs)

    return figs


def weights_tracking_error_report(multi_portfolio_data: MultiPortfolioData,
                                  strategy_idx: int = 0,
                                  benchmark_idx: int = 1,
                                  group_data: pd.Series = None,
                                  group_order: List[str] = None,
                                  group_data_short: pd.Series = None,
                                  group_order_short: List[str] = None,
                                  time_period: TimePeriod = None,
                                  perf_params: PerfParams = PERF_PARAMS,
                                  regime_params: BenchmarkReturnsQuantileRegimeSpecs = REGIME_PARAMS,
                                  add_benchmarks_to_navs: bool = True,
                                  figsize: Tuple[float, float] = (11.7, 8.3),
                                  var_format: str = '{:.1%}',
                                  **kwargs
                                  ) -> Tuple[Dict[str, plt.Figure], Dict[str, pd.DataFrame]]:

    regime_benchmark = multi_portfolio_data.benchmark_prices.columns[0]
    benchmark_price = multi_portfolio_data.benchmark_prices[regime_benchmark]

    figs = {}
    dfs = {}
    with sns.axes_style('darkgrid'):

        # navs + ra table
        fig, ax = plt.subplots(1, 1, figsize=figsize, tight_layout=True)
        figs['navs'] = fig
        multi_portfolio_data.plot_nav(regime_benchmark=regime_benchmark,
                                      time_period=time_period,
                                      perf_params=perf_params,
                                      regime_params=regime_params,
                                      add_benchmarks_to_navs=add_benchmarks_to_navs,
                                      title=f"Cumulative performance with background colors using bear/normal/bull "
                                            f"regimes of {regime_benchmark} {regime_params.freq}-returns",
                                      ax=ax,
                                      **kwargs)

        fig, ax = plt.subplots(1, 1, figsize=figsize, tight_layout=True)
        figs['ra_table'] = fig
        ra_perf_table = multi_portfolio_data.plot_ra_perf_table(benchmark_price=benchmark_price,
                                                                add_benchmarks_to_navs=add_benchmarks_to_navs,
                                                                perf_params=perf_params,
                                                                time_period=time_period,
                                                                add_turnover=True,
                                                                ax=ax,
                                                                **kwargs)
        dfs['ra_perf_table'] = ra_perf_table

        # strategy weights
        strategy_data = multi_portfolio_data.portfolio_datas[strategy_idx]
        weight_kwargs = dict(is_grouped=True, time_period=time_period, add_total=False, is_input_weights=True)
        exposures_short = strategy_data.get_weights(group_data=group_data_short, group_order=group_order_short,
                                                    **weight_kwargs)
        exposures_long = strategy_data.get_weights(group_data=group_data, group_order=group_order,
                                                    **weight_kwargs)
        fig, axs = plt.subplots(1, 2, figsize=figsize, tight_layout=True)
        qis.set_suptitle(fig, title=f"{strategy_data.ticker} Weights")
        figs['strategy_weights'] = fig
        plot_exposures(exposures_short=exposures_short,
                       exposures_long=exposures_long,
                       ylabel='Weights',
                       var_format=var_format,
                       axs=axs,  **kwargs)

        rc_kwargs = dict(covar_dict=multi_portfolio_data.covar_dict, freq='QE')
        # strategy risk contributions
        risk_contributions_short = strategy_data.compute_risk_contributions_implied_by_covar(group_data=group_data_short,
                                                                                             group_order=group_order_short,
                                                                                             **rc_kwargs)
        risk_contributions_long = strategy_data.compute_risk_contributions_implied_by_covar(group_data=group_data,
                                                                                            group_order=group_order,
                                                                                            **rc_kwargs)
        # ungrouped
        dfs['strategy_risk_contributions'] = strategy_data.compute_risk_contributions_implied_by_covar(**rc_kwargs)


        fig, axs = plt.subplots(1, 2, figsize=figsize, tight_layout=True)
        qis.set_suptitle(fig, title=f"{strategy_data.ticker} Risk Contributions")
        figs['strategy_var'] = fig
        plot_exposures(exposures_short=qis.df_to_weight_allocation_sum1(risk_contributions_short),
                       exposures_long=qis.df_to_weight_allocation_sum1(risk_contributions_long),
                       ylabel='Risk Contributions',
                       var_format=var_format,
                       axs=axs, **kwargs)

        # benchmark weights
        benchmark_data = multi_portfolio_data.portfolio_datas[benchmark_idx]
        benchmark_exposures_short = benchmark_data.get_weights(group_data=group_data_short, group_order=group_order_short,
                                                               **weight_kwargs)
        benchmark_exposures_long = benchmark_data.get_weights(group_data=group_data, group_order=group_order,
                                                              **weight_kwargs)

        fig, axs = plt.subplots(1, 2, figsize=figsize, tight_layout=True)
        qis.set_suptitle(fig, title=f"{benchmark_data.ticker} Weights")
        figs['benchmark_weights'] = fig
        plot_exposures(exposures_short=benchmark_exposures_short,
                       exposures_long=benchmark_exposures_long,
                       ylabel='Weights',
                       var_format=var_format,
                       axs=axs, **kwargs)

        # benchmark var
        benchmark_risk_contributions_short = benchmark_data.compute_risk_contributions_implied_by_covar(
            group_data=group_data_short,
            group_order=group_order_short,
            **rc_kwargs)
        benchmark_risk_contributions_long = benchmark_data.compute_risk_contributions_implied_by_covar(
            group_data=group_data,
            group_order=group_order,
            **rc_kwargs)
        # ungrouped
        dfs['benchmark_risk_contributions'] = benchmark_data.compute_risk_contributions_implied_by_covar(**rc_kwargs)

        fig, axs = plt.subplots(1, 2, figsize=figsize, tight_layout=True)
        qis.set_suptitle(fig, title=f"{benchmark_data.ticker} Risk Contributions")
        figs['benchmark_var'] = fig
        plot_exposures(exposures_short=qis.df_to_weight_allocation_sum1(benchmark_risk_contributions_short),
                       exposures_long=qis.df_to_weight_allocation_sum1(benchmark_risk_contributions_long),
                       ylabel='Risk Contributions',
                       var_format=var_format,
                       axs=axs, **kwargs)

        # turnover
        fig, ax = plt.subplots(1, 1, figsize=figsize, tight_layout=True)
        figs['turnover'] = fig
        multi_portfolio_data.plot_turnover(ax=ax,
                                           time_period=time_period,
                                           #turnover_rolling_period=260,
                                           #freq_turnover=None,
                                           **kwargs)

        fig, ax = plt.subplots(1, 1, figsize=figsize, tight_layout=True)
        figs['tre_time_series'] = fig
        multi_portfolio_data.plot_tre_time_series(strategy_idx=strategy_idx,
                                                  benchmark_idx=benchmark_idx,
                                                  ax=ax,
                                                  time_period=time_period,
                                                  **kwargs)

        # brinson
        fig, axs = plt.subplots(1, 2, figsize=figsize, tight_layout=True)
        figs['brinson'] = fig
        axs = [axs[0], axs[1], None, None, None]
        multi_portfolio_data.plot_brinson_attribution(strategy_idx=strategy_idx,
                                                      benchmark_idx=benchmark_idx,
                                                      time_period=time_period,
                                                      freq=None,
                                                      axs=axs,
                                                      total_column='Total Sum',
                                                      is_exclude_interaction_term=True,
                                                      **kwargs)

    return figs, dfs


def plot_exposures(exposures_short: pd.DataFrame,
                   exposures_long: pd.DataFrame,
                   axs: List[plt.Subplot],
                   ylabel: str = 'weights',
                   var_format: str = '{:.1%}',
                   hue_var_name: str = 'asset class',
                   **kwargs
                   ) -> None:
    qis.plot_stack(df=exposures_short,
                   use_bar_plot=True,
                   legend_stats=qis.LegendStats.AVG_NONNAN_LAST,
                   var_format=var_format,
                   colors=qis.get_n_sns_colors(n=len(exposures_short.columns)),
                   ax=axs[0],
                   **qis.update_kwargs(kwargs, dict(bbox_to_anchor=(0.5, 1.01), ncols=1,
                                                    framealpha=0.9)))

    qis.df_boxplot_by_columns(df=exposures_long,
                              hue_var_name=hue_var_name,
                              y_var_name=ylabel,
                              ylabel=ylabel,
                              showmedians=True,
                              add_y_median_labels=True,
                              yvar_format=var_format,
                              x_rotation=90,
                              colors=qis.get_n_sns_colors(n=len(exposures_long.columns)),
                              y_limits=(0.0, None),
                              ax=axs[1],
                              **kwargs)
