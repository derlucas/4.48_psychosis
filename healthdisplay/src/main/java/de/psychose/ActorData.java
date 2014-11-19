package de.psychose;

/**
 * @author: lucas
 * @date: 17.11.14 21:07
 */
public class ActorData {

    private PulseData pulseData = new PulseData();
    private int airflow;
    private int ekg;
    private int emg;
    private float temperature;
    private boolean tommyHeartbeat;

    private long timestampPulse = 0;
    private long timestampTommyPulse = 0;
    private long timestampEkg = 0;
    private long timestampEmg = 0;
    private long timestampTemperature = 0;
    private long timestampBreath = 0;

    // TODO: hier die timestamps setzen wann letztes mal geändert,
    // dann kann ich in ActorDisplay im Timer einfach prüfen ob differenz > timeout, dann rot setzen


    public void setTimestampPulse() {
        this.timestampPulse = System.currentTimeMillis();
    }
    public PulseData getPulseData() {
        return pulseData;
    }

    public void setPulseData(PulseData pulseData) {
        this.pulseData = pulseData;
        this.timestampPulse = System.currentTimeMillis();
    }

    public int getAirflow() {
        return airflow;
    }

    public void setAirflow(int airflow) {
        this.airflow = airflow;
        this.timestampBreath = System.currentTimeMillis();
    }

    public int getEkg() {
        return ekg;
    }

    public void setEkg(int ekg) {
        this.ekg = ekg;
        this.timestampEkg = System.currentTimeMillis();
    }

    public int getEmg() {
        return emg;
    }

    public void setEmg(int emg) {
        this.emg = emg;
        this.timestampEmg = System.currentTimeMillis();
    }

    public float getTemperature() {
        return temperature;
    }

    public void setTemperature(float temperature) {
        this.temperature = temperature;
        this.timestampTemperature = System.currentTimeMillis();
    }

    public boolean getTommyHeartbeat() {
        return tommyHeartbeat;
    }

    public void setTommyHeartbeat(boolean tommyHeartbeat) {
        this.tommyHeartbeat = tommyHeartbeat;
        this.timestampTommyPulse = System.currentTimeMillis();
    }

    public long getTimestampPulse() {
        return timestampPulse;
    }

    public long getTimestampEkg() {
        return timestampEkg;
    }

    public long getTimestampEmg() {
        return timestampEmg;
    }

    public long getTimestampTemperature() {
        return timestampTemperature;
    }

    public long getTimestampBreath() {
        return timestampBreath;
    }
}
