{{/*
Expand the name of the chart.
*/}}
{{- define "cas-airflow-dag-trigger.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "cas-airflow-dag-trigger.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "cas-airflow-dag-trigger.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "cas-airflow-dag-trigger.labels" -}}
helm.sh/chart: {{ include "cas-airflow-dag-trigger.chart" . }}
{{ include "cas-airflow-dag-trigger.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "cas-airflow-dag-trigger.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cas-airflow-dag-trigger.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "cas-airflow-dag-trigger.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "cas-airflow-dag-trigger.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
Gets the prefix of the namespace. (09269b, ... )
*/}}
{{- define "cas-airflow-dag-trigger.namespacePrefix" }}
{{- (split "-" .Release.Namespace)._0 | trim -}}
{{- end }}

{{/*
Gets the suffix of the namespace. (-dev, -tools, ... )
*/}}
{{- define "cas-airflow-dag-trigger.namespaceSuffix" }}
{{- (split "-" .Release.Namespace)._1 | trim -}}
{{- end }}

{{/* 
Looks up the artifactory service account and 
generates the image pull secret
*/}}
{{- define "cas-airflow-dag-trigger.imagePullSecrets" }}
{{- $artSa := (lookup "artifactory.devops.gov.bc.ca/v1alpha1" "ArtifactoryServiceAccount" .Release.Namespace .Values.artifactoryServiceAccount) }}
{{- if $artSa.spec }}
- name: artifacts-pull-{{ .Values.artifactoryServiceAccount }}-{{ $artSa.spec.current_plate }}
{{- else }}
{{/*
When running helm template, or using --dry-run, lookup returns an empty object
*/}}
- name: image-pull-secret-here
{{- end }}
{{- end }}
