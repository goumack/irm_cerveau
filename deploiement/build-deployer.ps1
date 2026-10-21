<#
.SYNOPSIS
  Construit l'image vgg16-tumeur dans le cluster OpenShift (build binaire Docker) et la déploie.

.EXAMPLE
  .\build-deployer.ps1 -Version 1.0.0
  .\build-deployer.ps1 -Version 1.0.1 -Namespace senia-surveillance-gpu

  Prérequis : oc login --token=... --server=https://api.origins.heritage.africa:6443
#>
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$Namespace = "senia-surveillance-gpu",
    [string]$OC = "C:\Users\baye.niang\Desktop\oc.exe"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Etape($message) { Write-Host "`n==> $message" -ForegroundColor Cyan }
function Oc { & $OC @args; if ($LASTEXITCODE -ne 0) { throw "Échec : oc $args" } }

if (-not (Test-Path "vgg16-tumeur/1/model.onnx")) { throw "vgg16-tumeur/1/model.onnx introuvable : exécuter d'abord le notebook." }

Etape "Connexion et namespace"
Oc whoami
Oc project $Namespace

Etape "1/4 BuildConfig"
& $OC get bc vgg16-tumeur 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Oc new-build --name=vgg16-tumeur --strategy=docker --binary --to=vgg16-tumeur:latest
} else {
    Write-Host "BuildConfig vgg16-tumeur déjà présent."
}

Etape "2/4 Construction de l'image dans le cluster"
Oc start-build vgg16-tumeur --from-dir=. --follow --wait

Etape "3/4 Tag de version $Version"
Oc tag vgg16-tumeur:latest "vgg16-tumeur:$Version"

Etape "4/4 Déploiement"
$image = "image-registry.openshift-image-registry.svc:5000/$Namespace/vgg16-tumeur:$Version"
Oc apply -f openshift/vgg16-tumeur.yaml
Oc set image deployment/vgg16-tumeur api=$image
Oc rollout status deployment/vgg16-tumeur --timeout=300s

$hote = & $OC get route vgg16-tumeur -o jsonpath="{.spec.host}"
Write-Host "`nAPI déployée ($image) : https://$hote" -ForegroundColor Green
Write-Host "Documentation : https://$hote/docs"
