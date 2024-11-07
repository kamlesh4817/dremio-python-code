# working copy from Max - 11/7
# This file is a template values file that should be used to install the Dremio EE Helm chart.
# The contents of this file should be customized to match the desired configuration.
# DO NOT USE THIS FILE AS-IS. IT IS A TEMPLATE ONLY.

# =================================
# Dremio coordinators and executors
# =================================

# Change image to match your repository
image: quay.io/dremio/dremio-ee
imageTag: 25.2.0
imagePullPolicy: IfNotPresent

# Uncomment and change if you want to use a private registry
imagePullSecrets:
 - dremiopullsecret

# Change the following values to match your environment
distStorage:
  type: azureStorage
  azureStorage:
    accountName: "maxmargalithstorage"
    filesystem: "dremio-bagpipe-dist"
    path: "/"
    credentials:
      accessKey: "<REDACTED>"

coordinator:
  # web:
  #   port: 9047
  #   tls:
  #     enabled: true
  #     secret: dremio-tls-secret

  nodeSelector:
    agentpool: dremiopool
  serviceAccount: dremio-lakehouse
  resources:
    requests:
      cpu: 3
      memory: 8000Mi
    limits:
      memory: 8000Mi
  
  extraStartParams: >-
    -Ddremio.log.path=/opt/dremio/data/log
    -Ddremio.debug.sysopt.dremio.catalog.private.preview.enabled=true
    -Ddremio.debug.sysopt.token.jwt-access-token.enabled=true
    -Ddremio.debug.sysopt.auth.personal-access-tokens.enabled=true

executor:
  nodeSelector:
    agentpool: dremiopool
  serviceAccount: dremio-lakehouse
  count: 1
  resources:
    requests:
      cpu: "3"
      memory: 16000Mi
    limits:
      memory: 16000Mi

#  volumeSize: 4Gi
#  cloudCache:
#    volumes:
#      - size: 4Gi

zookeeper:
  nodeSelector: 
    agentpool: infrapool
  count: 1
  serviceAccount: dremio-lakehouse
#  volumeSize: 1Gi

service:
  type: LoadBalancer

  # These values, when defined and not empty, override the provided shared annotations and labels.
  # Uncomment only if you are trying to override the chart's shared values.
  #annotations: {}
  #labels: {}

  # If the loadBalancer supports sessionAffinity and you have more than one coordinator,
  # uncomment the below line to enable session affinity.
  #sessionAffinity: ClientIP

  # Enable the following flag if you wish to route traffic through a shared VPC
  # for the LoadBalancer's external IP.
  # The chart is setup for internal IP support for AKS, EKS, GKE.
  # For more information, see https://kubernetes.io/docs/concepts/services-networking/service/#internal-load-balancer
  #internalLoadBalancer: true

  # If you have a static IP allocated for your load balancer, uncomment the following
  # line and set the IP to provide the static IP used for the load balancer.
  # Note: The service type must be set to LoadBalancer for this value to be used.
  #loadBalancerIP: 0.0.0.0


# =================================
# Dremio Lakehouse Catalog server
# =================================

catalog:

  # Change image to match your repository
  image:
    repository: quay.io/dremio/dremio-ee-catalog-server-private-preview
    tag: 25.2.0

  # Uncomment and change if you want to use a private registry
  #imagePullSecrets:
  #  - name: registry-creds

  serviceAccount:
    name: dremio-lakehouse
    create: false

  nodeSelector:
    agentpool: nessiepool
  resources:
    requests:
      cpu: 1
      memory: 2Gi
    limits:
      cpu: 1
      memory: 2Gi

  imagePullSecrets:
    - name: dremiopullsecret


# Uncomment to enable the Iceberg REST API, then adjust the configuration as needed
  catalog:
    enabled: true
    # iceberg:
    #   objectStoresHealthCheckEnabled: true
    #   defaultWarehouse: dremio-catalog
    #   warehouses:
    #     - name: dremio-catalog
    #       location: abfss://dremio-catalog@maxmargalithstorage.dfs.core.windows.net
    # storage:
    #   adls:
    #     defaultOptions:
    #       endpoint: https://maxmargalithstorage.dfs.core.windows.net/dremio-catalog
    #       authType: SAS_TOKEN # STORAGE_SHARED_KEY
    #       sasTokenSecret:
    #         # -- Name of the secret containing the SAS token.
    #         name: dremio-catalog-adls-warehouse-sas
    #         # -- Secret key containing the SAS token.
    #         sasToken: sasTokenSecret
  
# OLD: kubectl create secret generic dremio-catalog-adls-warehouse-sas -n dremio-lakehouse --from-literal sasTokenSecret="sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupyx&se=2025-01-11T18:08:52Z&st=2024-09-04T09:08:52Z&spr=https&sig=tIvKVcvUTQ0%2BodZ7MGFlmxl%2FUxj8MHVnRk2LB2xkgXg%3D"
# NEW: kubectl create secret generic dremio-catalog-adls-warehouse-sas -n dremio-lakehouse --from-literal sasTokenSecret="sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupyx&se=2024-12-15T20:01:26Z&st=2024-10-15T11:01:26Z&spr=https&sig=Y7OI%2FmoeLI0dxCiJW3ytqt4O7v%2Be1ZDaqV7prI8x1aA%3D"
# kubectl create secret generic dremio-catalog-s3-warehouse-creds -n dremio-lakehouse --from-literal awsAccessKeyId=$AWS_ACCESS_KEY_ID  --from-literal awsSecretAccessKey=$AWS_SECRET_ACCESS_KEY

    iceberg:
      objectStoresHealthCheckEnabled: true
      defaultWarehouse: dremio-catalog
      warehouses:
        - name: dremio-catalog
          location: s3://max-margalith-test-s3/dremio-catalog
    storage:
      s3:
        buckets:
          - name: max-margalith-test-s3
            region: eu-central-1
            accessKeySecret:
              name: dremio-catalog-s3-warehouse-creds
              awsAccessKeyId: awsAccessKeyId
              awsSecretAccessKey: awsSecretAccessKey
  # advancedConfig:
  #   quarkus.oidc.jwks-path: "https://dremio-client.germanywestcentral.cloudapp.azure.com:9047/oauth/discovery/jwks.json"


# =================================
# MongoDB cluster
# =================================

mongodb:
  nodeSelector:
    agentpool: nessiepool
  replicaCount: 1
  persistence:
    volumeClaimTemplates:
      requests:
        storage: 2Gi
  resources:
    requests:
      cpu: 1
      memory: 512Mi
    limits:
      memory: 1024Mi
