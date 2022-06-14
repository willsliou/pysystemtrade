from collections import namedtuple
from copy import copy

from syscore.interactive import get_field_names_for_named_tuple
from syscore.objects import arg_not_supplied, failure
from sysdata.config.production_config import get_production_config
from sysdata.data_blob import dataBlob
from sysobjects.futures_per_contract_prices import futuresContractPrices

priceFilterConfig = namedtuple('priceFilterConfig',
                               ['ignore_future_prices',
                                'ignore_prices_with_zero_volumes',
                                'ignore_zero_prices',
                                'ignore_negative_prices',
                                'max_price_spike',
                                'dont_sample_daily_if_intraday_fails'])


def apply_price_cleaning(data: dataBlob,
                          broker_prices_raw: futuresContractPrices,
                          cleaning_config = arg_not_supplied):

    if broker_prices_raw is failure:
        return failure

    cleaning_config = get_config_for_price_filtering(data =data,
                                                     cleaning_config=cleaning_config)

    broker_prices = copy(broker_prices_raw)

    ## It's important that the data is in local time zone so that this works
    if cleaning_config.ignore_future_prices:
        broker_prices = broker_prices.remove_future_data()

    if cleaning_config.ignore_prices_with_zero_volumes:
        broker_prices = broker_prices.remove_zero_volumes()

    if cleaning_config.ignore_zero_prices:
        ## need to implement
        broker_prices = broker_prices.remove_zero_prices()

    if cleaning_config.ignore_negative_prices:
        ## need to implement
        broker_prices = broker_prices.remove_negative_prices()

    return broker_prices


def get_config_for_price_filtering(data: dataBlob,
                                   cleaning_config: priceFilterConfig  = arg_not_supplied)\
        -> priceFilterConfig:

    if cleaning_config is not arg_not_supplied:
        ## override
        return cleaning_config

    production_config = get_production_config()

    ignore_future_prices = production_config.get_element_or_missing_data('ignore_future_prices')
    ignore_prices_with_zero_volumes = production_config.get_element_or_missing_data('ignore_future_prices')
    ignore_zero_prices = production_config.get_element_or_missing_data('ignore_zero_prices')
    ignore_negative_prices = production_config.get_element_or_missing_data('ignore_negative_prices')
    max_price_spike = production_config.get_element_or_missing_data('max_price_spike')
    dont_sample_daily_if_intraday_fails = production_config.get_element_or_missing_data('dont_sample_daily_if_intraday_fails')

    any_missing = any([x is arg_not_supplied for x in [ignore_future_prices, ignore_prices_with_zero_volumes, ignore_zero_prices, ignore_negative_prices,
                                                       dont_sample_daily_if_intraday_fails, max_price_spike]])

    if any_missing:
        error = 'Missing config items for price filtering - have you deleted from defaults.yaml?'
        data.log.critical(error)
        raise Exception(error)

    cleaning_config =  priceFilterConfig(ignore_zero_prices=ignore_zero_prices,
                             ignore_negative_prices=ignore_negative_prices,
                             ignore_future_prices=ignore_future_prices,
                             ignore_prices_with_zero_volumes=ignore_prices_with_zero_volumes,
                             max_price_spike=max_price_spike,
                             dont_sample_daily_if_intraday_fails=dont_sample_daily_if_intraday_fails)

    return cleaning_config


def interactively_get_config_overrides_for_cleaning(data) -> priceFilterConfig:
    default_config = get_config_for_price_filtering(data)
    print("Data cleaning configuration: (press enter for defaults)")
    new_config = get_field_names_for_named_tuple(default_config)

    return new_config