import torch
import torch.nn as nn


class GraphConvolution(nn.Module):

    def __init__(self, in_features, out_features):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x, adjacency):

        x = self.linear(x)

        x = torch.einsum(
            "nm,btmf->btnf",
            adjacency,
            x
        )

        return x


class GCNGRU(nn.Module):

    def __init__(
        self,
        input_features=4,
        gcn_hidden=32,
        gru_hidden=64,
        output_features=4,
        dropout=0.15
    ):

        super().__init__()

        self.output_features = output_features

        self.gcn1 = GraphConvolution(
            input_features,
            gcn_hidden
        )

        self.gcn2 = GraphConvolution(
            gcn_hidden,
            gcn_hidden
        )

        self.dropout = nn.Dropout(dropout)
        self.activation = nn.ReLU()

        self.gru = nn.GRU(
            input_size=gcn_hidden,
            hidden_size=gru_hidden,
            num_layers=1,
            batch_first=True
        )

        self.output_layer = nn.Linear(
            gru_hidden,
            output_features
        )

    def forward(self, x, adjacency):

        x = self.gcn1(x, adjacency)
        x = self.activation(x)
        x = self.dropout(x)

        x = self.gcn2(x, adjacency)
        x = self.activation(x)

        batch_size = x.shape[0]
        time_steps = x.shape[1]
        nodes = x.shape[2]
        hidden_size = x.shape[3]

        x = x.permute(0, 2, 1, 3)

        x = x.reshape(
            batch_size * nodes,
            time_steps,
            hidden_size
        )

        gru_output, hidden_state = self.gru(x)

        x = hidden_state[-1]

        x = self.output_layer(x)

        x = x.reshape(
            batch_size,
            nodes,
            self.output_features
        )

        return x
