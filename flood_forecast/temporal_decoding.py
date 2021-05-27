
import torch


def decoding_function(model, src: torch.Tensor, trg: torch.Tensor, forecast_length: int, src_temp: torch.Tensor,
                      tar_temp: torch.Tensor, unknown_cols_st: int, decoder_seq_len: int, max_len: int, device: str):
    """This function is responsible for decoding models that use `TemporalLoader` data. The basic logic of this
    function is as follows. The data to the encoder (e.g. src) is not modified at each step of the decoding process.
    Instead only the data to the decoder (e.g. the masked trg) is changed when forecasting max_len > forecast_length.
    New data is appended (forecast_len == 2) (decoder_seq==10) (max==20) (20 (8)->2 First 8 should

    :param model: The PyTorch time series forecasting model that you want to use forecasting on.
    :type model: `torch.nn.Module`
    :param src: The forecast_history tensor. Should be of dimension (batch_size, forecast_history, n_time_series).
    Ocassionally batch_size will not be present so at some points it will only be (forecast_history, n_time_series)
    :type src: torch.Tensor
    :param trg: The target tensor. Should be of dimension (batch_size, hours_to_forecast, n_time_series)
    :type trg: torch.Tensor
    :param forecast_length: The of length of the forecast the model makes at each forward pass.
    :type forecast_length: torch.Tensor
    :param src_temp: The temporal features for the forecast_history steps
    :type src_temp: int
    :param tar_temp: The target's temporal feats. This should have a shape of (batch_size, max_len+diff, n_time_series)
    :type tar_temp: torch.Tensor
    :param unknown_cols_st: The unknown columns
    :type unknown_cols_st: int
    :param decoder_seq_len: The length of the sequence passed into the decoder
    :type decoder_seq_len: int
    :param max_len: The total number of time steps to forecast
    :type max_len: int
    :return: The forecasted values of shape (batch_size, max_len, n_targets)
    :rtype: torch.Tensor
    """
    n_target = model.c_out
    if len(src.shape) == 2:
        # We assume batch_size is missing in this case
        # We add the batch_size dimension back
        src = src.unsqueeze(0)
        trg = trg.unsqueeze(0)
        src_temp = src_temp.unsqueeze(0)
        tar_temp = tar_temp.unsqueeze(0)
    out1 = torch.zeros_like(trg[:, :max_len, :])
    filled_target = trg.clone()[:, 0:decoder_seq_len, :].to(device)
    src = src.to(device)
    trg = trg.to(device)
    src_temp = src_temp.to(device)
    tar_temp = tar_temp.to(device)
    filled_target[:, -forecast_length:, :] = torch.zeros_like(filled_target[:, -forecast_length:, :n_target]).to(device)
    # Useless variable to avoid long line error..
    d = decoder_seq_len
    print("Filled target below")
    print(filled_target[:, -forecast_length:, :].shape)
    print(trg[:, d - forecast_length:decoder_seq_len, :].shape)
    filled_target = filled_target.to(device)
    # assert filled_target[:, -forecast_length:, :].any() != trg[:, d - forecast_length:decoder_seq_len, :].any()
    assert filled_target[0, -decoder_seq_len, 0] != trg[0, -decoder_seq_len, 0]
    assert filled_target[0, -1, 0] != trg[0, -1, 0]
    for i in range(0, max_len, forecast_length):
        # CHANGE THIS LINE !!
        residual = decoder_seq_len
        filled_target = filled_target[:, -residual:, :]
        if residual != decoder_seq_len:
            out = model(src, src_temp, filled_target, tar_temp[:, -residual:, :])
        else:
            out = model(src, src_temp, filled_target, tar_temp[:, i:i + residual, :])
        residual1 = forecast_length if i + forecast_length <= max_len else max_len % forecast_length
        out1[:, i: i + residual1, :n_target] = out[:, -residual1:, :]
        filled_target1 = torch.zeros_like(filled_target[:, 0:forecast_length * 2, :])
        if filled_target1.shape[1] == forecast_length * 2:
            filled_target1[:, -forecast_length * 2:-forecast_length, :n_target] = out[:, -forecast_length:, :]
            filled_target = torch.cat((filled_target, filled_target1), dim=1)
        assert out1[0, 0, 0] != 0
        assert out1[0, 0, 0] != 0
    return out1[:, -max_len:, :n_target]
