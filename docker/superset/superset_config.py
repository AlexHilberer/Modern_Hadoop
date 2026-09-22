SQLALCHEMY_DATABASE_URI = "postgresql://superset:superset@postgres:5432/superset"

# Fixed dev-only key so sessions survive container restarts -- not for
# production use, consistent with the rest of this fun/portfolio project.
SECRET_KEY = "modern-hadoop-dev-secret-key-not-for-production"
