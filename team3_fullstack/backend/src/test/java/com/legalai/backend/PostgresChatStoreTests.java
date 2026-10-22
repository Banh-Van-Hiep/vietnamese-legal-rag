package com.legalai.backend;

import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

/** Same behavioral suite on real PostgreSQL, only when an explicit test URL is supplied. */
@EnabledIfSystemProperty(named = "test.postgres.url", matches = "jdbc:postgresql:.*")
class PostgresChatStoreTests extends ChatStoreTests {
    private DriverManagerDataSource admin;
    private String schema;
    @Override protected DriverManagerDataSource dataSource() {
        String url = System.getProperty("test.postgres.url");
        String user = System.getProperty("test.postgres.user", "vlra41");
        String password = System.getenv().getOrDefault("TEST_POSTGRES_PASSWORD", "");
        admin = new DriverManagerDataSource(url, user, password);
        schema = "vlra41_" + UUID.randomUUID().toString().replace("-", "");
        new JdbcTemplate(admin).execute("CREATE SCHEMA " + schema);
        return new DriverManagerDataSource(url + (url.contains("?") ? "&" : "?") + "currentSchema=" + schema, user, password);
    }
    @AfterEach void removeOwnSchema() {
        if (schema != null && schema.matches("vlra41_[0-9a-f]{32}")) {
            new JdbcTemplate(admin).execute("DROP SCHEMA " + schema + " CASCADE");
        }
    }
}
