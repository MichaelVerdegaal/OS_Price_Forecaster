import pandas as pd
from pandas.core.dtypes.common import is_string_dtype
from sklearn.preprocessing import LabelEncoder
from queries import retrieve_events


def unpack_traits(traits: list):
    """
    Unpacks NFT traits into a processable formate
    :param traits: list of traits
    :return: processed traits
    """
    unpacked_traits = {}
    for trait in traits:
        trait_name = f"{trait['trait_type'].replace(' ', '_').lower()}"
        trait_value = trait['value']
        if isinstance(trait_value, str):
            unpacked_traits[f'{trait_name}_traitvalue'] = str(trait_value).lower()
        else:
            unpacked_traits[f'{trait_name}_traitvalue'] = trait_value
        unpacked_traits[f'{trait_name}_traitcount'] = trait['trait_count']
    return unpacked_traits


def unpack_sale(sale_object: dict, num_sales: int):
    """
    Unpacks sale object for the relevant information
    :param sale_object: dict with sale information
    :param num_sales: number of sales of the relevant item
    :return: dict with processed information
    """
    # date = sale_object['event_timestamp']  # TODO: this is harder to convert to a feature, so we'll leave it for now
    wei = float(sale_object['total_price'])
    ether = wei / (10 ** 18)
    return {'num_sales': num_sales, 'price': ether}


def clean_dataframe(df: pd.DataFrame):
    """
    Processes the values in the dataframe so it can be entered into a neural network
    :param df: Dataframe to clean
    :return: Cleaned dataframe
    """
    enc = LabelEncoder()
    # One-hot encode all categorical traits
    for col in df.filter(like='traitvalue').columns:
        if is_string_dtype(df[col]):
            df[col].fillna('none', inplace=True)
            one_hot = pd.get_dummies(df[col])
            df = df.drop(col, axis=1)
            df = df.join(one_hot, rsuffix=f'{col}_')

    # Label encode all numerical traits
    for col in df.filter(like='traitcount').columns:
        total_nan = int(df[col].isna().sum())
        df[col].fillna(total_nan, inplace=True)
        df[col] = enc.fit_transform(df[col])
    return df


def build_dataset(item_collection: list):
    """
    Builds the final dataset of the collected assets
    :param item_collection: list of NFT's
    :return: dataframe
    """
    dataset = []
    for item in item_collection:
        num_sales = item['num_sales']
        # Only if the item has any sales we'll continue
        if num_sales > 0:
            last_sale = item['last_sale']
            if last_sale:
                token_id = int(item['token_id'])
                print(f'{token_id=}')
                contract_address = item['asset_contract']['address']
                events = retrieve_events(contract_address, token_id)
                for event in events['asset_events']:
                    if event['event_type'] == 'successful':
                        traits = item['traits']
                        if isinstance(traits, dict):
                            item = {'token_id': token_id,
                                    'sales': unpack_sale(event, num_sales),
                                    'traits': unpack_traits(traits)}
                            dataset.append(item)

    df = pd.json_normalize(dataset)
    df = clean_dataframe(df)
    return df