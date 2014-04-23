package de.psychose;

import org.snmp4j.CommunityTarget;
import org.snmp4j.Snmp;
import org.snmp4j.TransportMapping;
import org.snmp4j.mp.SnmpConstants;
import org.snmp4j.smi.OID;
import org.snmp4j.smi.OctetString;
import org.snmp4j.smi.UdpAddress;
import org.snmp4j.smi.VariableBinding;
import org.snmp4j.transport.DefaultUdpTransportMapping;
import org.snmp4j.util.DefaultPDUFactory;
import org.snmp4j.util.TreeEvent;
import org.snmp4j.util.TreeUtils;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;

/**
 * @author: lucas
 * @date: 18.04.14 12:10
 */
public class SnmpStatClient {
    public static final String OID_COUNTER = "1.3.6.1.2.1.2.2.1.10";
    private final String host;
    private HashMap<Integer, Long> lastPorts = new HashMap<>();
    private HashMap<Integer, Long> sumPorts = new HashMap<>();

    private CommunityTarget getCommunityTarget() {
        CommunityTarget communityTarget = new CommunityTarget();
        communityTarget.setCommunity(new OctetString("public"));
        communityTarget.setVersion(SnmpConstants.version2c);
        communityTarget.setAddress(new UdpAddress(host));
        communityTarget.setTimeout(500);
        return communityTarget;
    }

    public SnmpStatClient(String host) {
        this.host = host;
    }

    public long getTrafficSum() {

        long sum = 0;

        try {
            final TransportMapping transportMapping = new DefaultUdpTransportMapping();
            transportMapping.listen();

            final Snmp snmp = new Snmp(transportMapping);
            final TreeUtils treeUtils = new TreeUtils(snmp, new DefaultPDUFactory());
            final List<TreeEvent> treeEventList = treeUtils.getSubtree(getCommunityTarget(), new OID(OID_COUNTER));

            for (TreeEvent treeEvent : treeEventList) {
                if (treeEvent.getStatus() == TreeEvent.STATUS_OK) {
                    for (VariableBinding binding : treeEvent.getVariableBindings()) {
                        int oid = binding.getOid().last();
                        long value = binding.getVariable().toLong();
                        long lastValue = 0;
                        if(lastPorts.containsKey(oid)) lastValue = lastPorts.get(oid);
                        long diff = value - lastValue;

                        if(diff > 0) {
                            sumPorts.put(oid, lastValue + diff);
                        }
                    }
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

        for(long port: sumPorts.values()) {
            sum+=port;
        }

        return sum;
    }

}
