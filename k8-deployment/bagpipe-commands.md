# created on 11/7/2024 for 180 days
# set environment variable
$DREMIO_PAT = "ZjZkl+24SYKcMCoUbadHCy+LT/VYE21vuIezRSPm9HB+UQLWF+0k/hSJnzThLw==" 
echo $DREMIO_PAT

# Add your IP to the Settings -> Networking -> Authorized IP ranges to get access to the cluster

helm pull oci://quay.io/dremio/dremio-ee-helm-private-preview --version=25.2.0

Dremio: http://dremio-client.germanywestcentral.cloudapp.azure.com:9047/
Dremio Catalog (Nessie): http://dremio-catalog-server-ext.germanywestcentral.cloudapp.azure.com:19120/

Username: kamlesh
PW: dremio123

kubectl get deployments --all-namespaces=true
kubectl get deployments --namespace dremio-lakehouse
kubectl describe deployment dremio-catalog-server --namespace dremio-lakehouse

Get Nessie token:
$DREMIO_URL_ENCODED_PAT = "ZjZkl%2B24SYKcMCoUbadHCy%2BLT%2FVYE21vuIezRSPm9HB%2BUQLWF%2B0k%2FhSJnzThLw%3D%3D" 
curl -X POST http://dremio-catalog-server-ext.germanywestcentral.cloudapp.azure.com:19120/oauth/token \
-d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange&scope=dremio.all&subject_token_type=urn:ietf:params:oauth:token-type:dremio:personal-access-token&subject_token=$DREMIO_URL_ENCODED_PAT" | jq -r .access_token

Using Iceberg REST:
spark-sql \
--packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,org.apache.iceberg:iceberg-aws-bundle:1.6.1 \
--conf spark.sql.catalog.nessie=org.apache.iceberg.spark.SparkCatalog \
--conf spark.sql.catalog.nessie.type=rest \
--conf spark.sql.catalog.nessie.uri=http://dremio-catalog-server-ext.germanywestcentral.cloudapp.azure.com:19120/iceberg/main \
--conf spark.sql.catalog.nessie.token="$NESSIE_TOKEN"

USE nessie;
SHOW NAMESPACES;
USE NAMESPACE <ns>;
SHOW TABLES;
CREATE TABLE abc AS SELECT 1 as col1;



spark-sql \
--packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,org.apache.iceberg:iceberg-aws-bundle:1.6.1,org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:0.99.0 \
--conf spark.sql.catalog.nessie=org.apache.iceberg.spark.SparkCatalog \
--conf spark.sql.catalog.nessie.catalog-impl=org.apache.iceberg.nessie.NessieCatalog \
--conf spark.sql.catalog.nessie.io-impl=org.apache.iceberg.io.ResolvingFileIO \
--conf spark.sql.catalog.nessie.uri=http://dremio-catalog-server-ext.germanywestcentral.cloudapp.azure.com:19120/api/v2 \
--conf spark.sql.catalog.nessie.ref=main \
--conf spark.sql.catalog.nessie.authentication.type=OAUTH2 \
--conf spark.sql.catalog.nessie.authentication.oauth2.client-id=nessie-cli \
--conf spark.sql.catalog.nessie.authentication.oauth2.grant-type=token_exchange \
--conf spark.sql.catalog.nessie.authentication.oauth2.token-exchange.subject-token=“$DREMIO_PAT” \
--conf spark.sql.catalog.nessie.authentication.oauth2.token-exchange.subject-token-type=urn:ietf:params:oauth:token-type:dremio:personal-access-token \
--conf spark.sql.catalog.nessie.authentication.oauth2.token-endpoint=http://dremio-client.germanywestcentral.cloudapp.azure.com:9047/oauth/token \
--conf spark.sql.catalog.nessie.authentication.oauth2.client-scopes=dremio.all \
--conf spark.sql.catalog.nessie.warehouse=s3://max-margalith-test-s3/dremio-catalog

