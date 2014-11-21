package de.psychose;

/**
 * @author: lucas
 * @date: 17.11.14 21:07
 */
public class ActorData {

    private String actor = "";
    private String caption = "";
    private PulseData pulseData = new PulseData();
    private int airflow;
    private int ekg;
    private int emg;
    private double temperature;
    private double temperatureOffset;
    private boolean tommyHeartbeat;

    private long timestampPulse = 0;
    private long timestampHeartbeat = 0;
    private long timestampOxygen = 0;
    private long timestampTommyHeartbeat = 0;
    private long timestampEkg = 0;
    private long timestampEmg = 0;
    private long timestampTemperature = 0;
    private long timestampBreath = 0;

    public ActorData(String actor, String caption) {
        this.actor = actor;
        this.caption = caption;
    }

    public String getActor() {
        return actor;
    }

    public String getCaption() {
        return caption;
    }

    public int getOxygen() {
        return pulseData.getOxygen();
    }

    public void setOxygen(int oxygen) {
        timestampOxygen = System.currentTimeMillis();
        pulseData.setOxygen(oxygen);
    }

    public boolean getHeartbeat() {
        return pulseData.getHeartbeat();
    }

    public void setHeartbeat(boolean heartbeat) {
        timestampHeartbeat = System.currentTimeMillis();
        pulseData.setHeartbeat(heartbeat);
    }

    public int getPulse() {
        return pulseData.getPulse();
    }

    public void setPulse(int pulse) {
        timestampPulse = System.currentTimeMillis();
        pulseData.setPulse(pulse);
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

    public double getTemperature() {
        return temperature;
    }

    public void setTemperature(double temperature) {
        this.temperature = temperature;
        this.timestampTemperature = System.currentTimeMillis();
    }

    public boolean getTommyHeartbeat() {
        return tommyHeartbeat;
    }

    public void setTommyHeartbeat(boolean tommyHeartbeat) {
        this.tommyHeartbeat = tommyHeartbeat;
        this.timestampTommyHeartbeat = System.currentTimeMillis();
    }

    public double getTemperatureOffset() {
        return temperatureOffset;
    }

    public void setTemperatureOffset(double temperatureOffset) {
        this.temperatureOffset = temperatureOffset;
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

    @Override
    public String toString() {
        return "ActorData{" +
                "actor='" + actor + '\'' +
                ", caption='" + caption + '\'' +
                ", airflow=" + airflow +
                ", ekg=" + ekg +
                ", emg=" + emg +
                ", temperature=" + temperature +
                ", temperatureOffset=" + temperatureOffset +
                ", tommyHeartbeat=" + tommyHeartbeat +
                ", timestampPulse=" + timestampPulse +
                ", timestampHeartbeat=" + timestampHeartbeat +
                ", timestampOxygen=" + timestampOxygen +
                ", timestampTommyHeartbeat=" + timestampTommyHeartbeat +
                ", timestampEkg=" + timestampEkg +
                ", timestampEmg=" + timestampEmg +
                ", timestampTemperature=" + timestampTemperature +
                ", timestampBreath=" + timestampBreath +
                '}';
    }
}
