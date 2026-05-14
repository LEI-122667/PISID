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
import com.maze.models.SoundData;

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

public class MazeSoundFragment extends Fragment {

    private LineChart lineChart;
    private OkHttpClient client;
    private String host, database, username, password;
    private List<SoundData> soundDataList = new ArrayList<>();
    
    private final Handler handler = new Handler();
    private Runnable refreshRunnable;

    public static MazeSoundFragment newInstance(String host, String database, String username, String password) {
        MazeSoundFragment fragment = new MazeSoundFragment();
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
        View view = inflater.inflate(R.layout.fragment_maze_sound, container, false);
        lineChart = view.findViewById(R.id.lineChartSound);
        client = new OkHttpClient();

        if (getArguments() != null) {
            host = getArguments().getString("host");
            database = getArguments().getString("database");
            username = getArguments().getString("username");
            password = getArguments().getString("password");
        }

        setupChart();

        refreshRunnable = new Runnable() {
            @Override
            public void run() {
                fetchSoundData();
                handler.postDelayed(this, 1000); // 1 segundo
            }
        };

        return view;
    }

    @Override
    public void onResume() {
        super.onResume();
        handler.post(refreshRunnable);
    }

    @Override
    public void onPause() {
        super.onPause();
        handler.removeCallbacks(refreshRunnable);
    }

    private void setupChart() {
        lineChart.getDescription().setEnabled(false);
        lineChart.setNoDataText("A carregar dados de som...");
        XAxis xAxis = lineChart.getXAxis();
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        lineChart.getAxisRight().setEnabled(false);
    }

    private void fetchSoundData() {
        if (host == null) return;
        String url = "http://" + host + "/api/get_sound_data.php";
        HttpUrl.Builder urlBuilder = HttpUrl.parse(url).newBuilder();
        try {
            urlBuilder.addQueryParameter("database", URLEncoder.encode(database, "UTF-8"));
            urlBuilder.addQueryParameter("username", username);
            urlBuilder.addQueryParameter("password", password);
        } catch (Exception e) { e.printStackTrace(); }

        Request request = new Request.Builder().url(urlBuilder.build()).build();
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) { Log.e("MazeSound", "Erro: " + e.getMessage()); }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                if (response.isSuccessful() && response.body() != null) {
                    String data = response.body().string();
                    try {
                        JSONObject json = new JSONObject(data);
                        JSONArray arr = json.getJSONArray("data");
                        soundDataList.clear();
                        for (int i = 0; i < arr.length(); i++) {
                            JSONObject obj = arr.getJSONObject(i);
                            soundDataList.add(new SoundData(obj.getInt("idsom"), (float) obj.getDouble("som")));
                        }
                        fetchMaxSound();
                    } catch (Exception e) { e.printStackTrace(); }
                }
            }
        });
    }

    private void fetchMaxSound() {
        String url = "http://" + host + "/api/get_max_sound_value.php";
        HttpUrl.Builder urlBuilder = HttpUrl.parse(url).newBuilder();
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
                    String data = response.body().string();
                    try {
                        JSONObject json = new JSONObject(data);
                        if (json.getBoolean("success")) {
                            JSONObject dataObj = json.getJSONObject("data");
                            float max = (float) dataObj.getDouble("maximo");
                            float offset = (float) dataObj.optDouble("offset", 0.0);
                            if (getActivity() != null) {
                                getActivity().runOnUiThread(() -> updateChart(soundDataList, max, offset));
                            }
                        }
                    } catch (Exception e) { e.printStackTrace(); }
                }
            }
        });
    }

    private void updateChart(List<SoundData> list, float maxVal, float offset) {
        if (list.isEmpty() || !isAdded()) return;

        ArrayList<Entry> entries = new ArrayList<>();
        ArrayList<Entry> maxLimit = new ArrayList<>();
        ArrayList<Entry> alertLimit = new ArrayList<>();

        float alertVal = maxVal - offset;
        float maxY = Float.MIN_VALUE;

        for (SoundData d : list) {
            float id = d.getId();
            float val = d.getValue();
            entries.add(new Entry(id, val));
            maxLimit.add(new Entry(id, maxVal));
            alertLimit.add(new Entry(id, alertVal));
            if (val > maxY) maxY = val;
        }

        ArrayList<ILineDataSet> sets = new ArrayList<>();
        sets.add(createSet(entries, "Som", Color.BLUE, true));
        sets.add(createSet(maxLimit, "Limite", Color.RED, false));
        sets.add(createSet(alertLimit, "Alerta", Color.rgb(255, 165, 0), false));

        lineChart.setData(new LineData(sets));
        YAxis left = lineChart.getAxisLeft();
        float top = Math.max(maxVal, maxY);
        left.setAxisMaximum(top + (top * 0.2f) + 5f);
        left.setAxisMinimum(0f);
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