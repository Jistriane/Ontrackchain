{{/*
   Ontrackchain Platform Helm Helpers — Milestone Pós-MVP 8 Sprint14
   Single Source of Truth: nomenclatura, selector labels, service ports
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "ontrackchain.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ontrackchain.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Common labels shared by all Ontrackchain resources
*/}}
{{- define "ontrackchain.labels" -}}
helm.sh/chart: {{ include "ontrackchain.chart" . }}
app.kubernetes.io/name: {{ include "ontrackchain.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: ontrackchain-platform
ontrackchain.io/sprint: s14-m8-helm
{{- end -}}

{{/*
Selector labels (used by Deployments / StatefulSets matchLabels)
*/}}
{{- define "ontrackchain.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ontrackchain.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
ontrackchain.io/component: {{ required "component label required" .Values._component }}
{{- end -}}

{{/*
Chart name + version
*/}}
{{- define "ontrackchain.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
ServiceAccount name
*/}}
{{- define "ontrackchain.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{ default (include "ontrackchain.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
{{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
FastAPI service port mapping (SSOT para 9 serviços + infra)
*/}}
{{- define "ontrackchain.port" -}}
{{- $svc := .service -}}
{{- $m := dict
  "case-management" 8001
  "auth-service" 8002
  "ai-service" 8003
  "investigation-api" 8004
  "mock-oidc" 8005
  "public-api" 8006
  "monitoring-api" 8007
  "compliance-api" 8008
  "report-api" 8009
  "postgres" 5432
  "prometheus" 9090
  "grafana" 3000
  "alertmanager" 9093
  "keycloak" 8080
  "traefik" 80
-}}
{{- printf "%d" (index $m $svc) -}}
{{- end -}}
