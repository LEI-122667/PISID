package com.maze.models;

import com.google.gson.annotations.SerializedName;

public class MinMaxValues {

    @SerializedName("minimo")
    private float minimo;
    @SerializedName("maximo")
    private float maximo;
    @SerializedName("offset_min")
    private float offsetMin;
    @SerializedName("offset_max")
    private float offsetMax;

    public MinMaxValues() {
    }

    public MinMaxValues(float minimo, float maximo, float offsetMin, float offsetMax) {
        this.minimo = minimo;
        this.maximo = maximo;
        this.offsetMin = offsetMin;
        this.offsetMax = offsetMax;
    }

    public float getMinimo() {
        return minimo;
    }

    public float getMaximo() {
        return maximo;
    }

    public float getOffsetMin() {
        return offsetMin;
    }

    public float getOffsetMax() {
        return offsetMax;
    }
}