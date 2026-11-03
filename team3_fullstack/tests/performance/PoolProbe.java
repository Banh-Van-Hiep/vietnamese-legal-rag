/** TEST ONLY: attaches to the owned test JVM; no public metrics endpoint. */
import com.sun.tools.attach.VirtualMachine;
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;
import javax.management.*;
import javax.management.remote.*;

class PoolProbe {
    public static void main(String[] args) throws Exception {
        var out = Path.of(args[1]);
        var vm = VirtualMachine.attach(args[0]);
        String address;
        try { address = vm.startLocalManagementAgent(); }
        finally { vm.detach(); }
        try (var connector = JMXConnectorFactory.connect(new JMXServiceURL(address))) {
            var server = connector.getMBeanServerConnection();
            var pools = server.queryNames(new ObjectName("com.zaxxer.hikari:type=Pool (*)"), null);
            if (pools.size() != 1) throw new IllegalStateException("Expected one test Hikari pool");
            var pool = pools.iterator().next();
            var threads = ManagementFactory.newPlatformMXBeanProxy(server, ManagementFactory.THREAD_MXBEAN_NAME, ThreadMXBean.class);
            var memory = ManagementFactory.newPlatformMXBeanProxy(server, ManagementFactory.MEMORY_MXBEAN_NAME, MemoryMXBean.class);
            Files.writeString(out.resolve("pool-samples.jsonl"), "");
            Files.writeString(out.resolve("pool-ready"), "ready");
            long end = System.nanoTime() + 120_000_000_000L;
            while (System.nanoTime() < end) {
                var names = new TreeSet<String>();
                for (var info : threads.getThreadInfo(threads.getAllThreadIds())) {
                    if (info != null && info.getThreadName().matches("pool-[0-9]+-thread-[0-9]+")) names.add(info.getThreadName());
                }
                String row = "{\"epoch_ms\":" + System.currentTimeMillis()
                    + ",\"active\":" + server.getAttribute(pool, "ActiveConnections")
                    + ",\"idle\":" + server.getAttribute(pool, "IdleConnections")
                    + ",\"total\":" + server.getAttribute(pool, "TotalConnections")
                    + ",\"awaiting\":" + server.getAttribute(pool, "ThreadsAwaitingConnection")
                    + ",\"jvm_threads\":" + threads.getThreadCount()
                    + ",\"jvm_used_bytes\":" + (memory.getHeapMemoryUsage().getUsed() + memory.getNonHeapMemoryUsage().getUsed())
                    + ",\"executor_threads\":" + names.size() + "}\n";
                Files.writeString(out.resolve("pool-samples.jsonl"), row, StandardOpenOption.APPEND);
                if (Files.exists(out.resolve("pool-stop"))) break;
                Thread.sleep(100);
            }
        }
    }
}
