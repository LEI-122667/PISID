package com.maze;

import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.components.YAxis;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;
import com.github.mikephil.charting.interfaces.datasets.ILineDataSet;
import com.google.gson.Gson;
import com.maze.models.MinMaxValues;
import com.maze.models.TempData;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.List;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class MazeTemperatureFragment extends Fragment {

    private LineChart lineChart;
    private OkHttpClient client;
    private String host, database, username, password;
    private List<TempData> tempDataList = new ArrayList<>();
    
    private final Handler handler = new Handler();
    private Runnable refreshRunnable;

    public static MazeTemperatureFragment newInstance(String host, String database, String username, String password) {
        MazeTemperatureFragment fragment = new MazeTemperatureFragment();
        Bundle args = new Bundle();
        args.putString("host", host);
        args.putString("database", database);
        args.putString("username", username);
        args.putString("password", password);
        fragment.setArguments(args);
        return fragment;
    }

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_maze_temperature, container, false);
        lineChart = view.findViewById(R.id.lineChartTemperature);
        client = new OkHttpClient();

        if (getArguments() != null) {
            host = getArguments().getString("host");
            database = getArguments().getString("database");
            username = getArguments().getString("username");
            password = getArguments().getString("password");
        }

        setupChart();

        // Configurar Runnable para atualização periódica
        refreshRunnable = new Runnable() {
            @Override
            public void run() {
                fetchTemperatureData();
                handler.postDelayed(this, 1000); // Atualiza de 1 em 1 segundo
            }
        };

        return view;
    }

    @Override
    public void onResume() {
        super.onResume();
        handler.post(refreshRunnable); // Inicia ao abrir
    }

    @Override
    public void onPause() {
        super.onPause();
        handler.removeCallbacks(refreshRunnable); // Para ao sair
    }

    private void setupChart() {
        lineChart.getDescription().setEnabled(false);
        lineChart.setNoDataText("A carregar dados...");
        XAxis xAxis = lineChart.getXAxis();
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        lineChart.getAxisRight().setEnabled(false);
    }

    private void fetchTemperatureData() {
        if (host == null) return;
        String tempUrl = "http://" + host + "/api/get_temperature_data.php";
        HttpUrl.Builder urlBuilder = HttpUrl.parse(tempUrl).newBuilder();
        try {
            urlBuilder.addQueryParameter("database", URLEncoder.encode(database, "UTF-8"));
            urlBuilder.addQueryParameter("username", username);
            urlBuilder.addQueryParameter("password", password);
        } catch (Exception e) { e.printStackTrace(); }

        Request request = new Request.Builder().url(urlBuilder.build()).build();
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) { Log.e("MazeTemp", "Erro: " + e.getMessage()); }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                if (response.isSuccessful() && response.body() != null) {
                    String responseData = response.body().string();
                    try {
                        JSONObject jsonResponse = new JSONObject(responseData);
                        JSONArray dataArray = jsonResponse.getJSONArray("data");
                        tempDataList.clear();
                        for (int i = 0; i < dataArray.length(); i++) {
                            JSONObject obj = dataArray.getJSONObject(i);
                            tempDataList.add(new TempData(obj.getInt("idtemperatura"), (float) obj.getDouble("temperatura")));
                        }
                        fetchMinMaxValues();
                    } catch (Exception e) { e.printStackTrace(); }
                }
            }
        });
    }

    private void fetchMinMaxValues() {
        String minMaxUrl = "http://" + host + "/api/get_min_max_temp_values.php";
        HttpUrl.Builder urlBuilder = HttpUrl.parse(minMaxUrl).newBuilder();
        try {
            urlBuilder.addQueryParameter("database", URLEncoder.encode(database, "UTF-8"));
            urlBuilder.addQueryParameter("username", username);
            urlBuilder.addQueryParameter("password", password);
        } catch (Exception e) { e.printStackTrace(); }

        Request request = new Request.Builder().url(urlBuilder.build()).build();
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {}

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                if (response.isSuccessful() && response.body() != null) {
                    String responseData = response.body().string();
                    try {
                        JSONObject jsonResponse = new JSONObject(responseData);
                        if (jsonResponse.getBoolean("success")) {
                            MinMaxValues minMax = new Gson().fromJson(jsonResponse.getJSONObject("data").toString(), MinMaxValues.class);
                            if (getActivity() != null) {
                                getActivity().runOnUiThread(() -> updateChart(tempDataList, minMax));
                            }
                        }
                    } catch (Exception e) { e.printStackTrace(); }
                }
            }
        });
    }

    private void updateChart(List<TempData> list, MinMaxValues minMax) {
        if (list.isEmpty() || !isAdded()) return;

        ArrayList<Entry> entries = new ArrayList<>();
        ArrayList<Entry> maxLimit = new ArrayList<>();
        ArrayList<Entry> minLimit = new ArrayList<>();
        ArrayList<Entry> maxAlert = new ArrayList<>();
        ArrayList<Entry> minAlert = new ArrayList<>();

        float maxVal = minMax.getMaximo();
        float minVal = minMax.getMinimo();
        float alertMax = maxVal - minMax.getOffsetMax();
        float alertMin = minVal + minMax.getOffsetMin();

        float minY = Float.MAX_VALUE;
        float maxY = Float.MIN_VALUE;

        for (TempData d : list) {
            float id = d.getID();
            float val = d.getValue();
            entries.add(new Entry(id, val));
            maxLimit.add(new Entry(id, maxVal));
            minLimit.add(new Entry(id, minVal));
            maxAlert.add(new Entry(id, alertMax));
            minAlert.add(new Entry(id, alertMin));
            if (val < minY) minY = val;
            if (val > maxY) maxY = val;
        }

        ArrayList<ILineDataSet> dataSets = new ArrayList<>();
        dataSets.add(createSet(entries, "Temp", Color.BLUE, true));
        dataSets.add(createSet(maxLimit, "Limite Max", Color.RED, false));
        dataSets.add(createSet(minLimit, "Limite Min", Color.RED, false));
        dataSets.add(createSet(maxAlert, "Alerta Max", Color.rgb(255, 165, 0), false));
        dataSets.add(createSet(minAlert, "Alerta Min", Color.rgb(255, 165, 0), false));

        lineChart.setData(new LineData(dataSets));
        YAxis leftAxis = lineChart.getAxisLeft();
        float top = Math.max(maxVal, maxY);
        float bottom = Math.min(minVal, minY);
        leftAxis.setAxisMaximum(top + (top * 0.1f) + 2f);
        leftAxis.setAxisMinimum(bottom - (bottom * 0.1f) - 2f);
        lineChart.invalidate();
    }

    private LineDataSet createSet(List<Entry> entries, String label, int color, boolean main) {
        LineDataSet set = new LineDataSet(entries, label);
        set.setColor(color);
        set.setDrawCircles(main);
        set.setDrawValues(false);
        set.setLineWidth(2f);
        if (main) set.setMode(LineDataSet.Mode.CUBIC_BEZIER);
        else set.enableDashedLine(10f, 5f, 0f);
        return set;
    }
}