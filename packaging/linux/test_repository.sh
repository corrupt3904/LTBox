#!/usr/bin/env bash
# Exercise the real repository generator with disposable, signed fixture packages.
set -euo pipefail

temporary_dir="$(mktemp -d)"
trap 'rm -rf "${temporary_dir}"' EXIT
export GNUPGHOME="${temporary_dir}/gnupg"
mkdir -m 0700 "${GNUPGHOME}"
export REPO_GPG_PASSPHRASE=ci-fixture-only
gpg --batch --pinentry-mode loopback --passphrase "${REPO_GPG_PASSPHRASE}" \
    --quick-generate-key 'LTBox CI fixture <ci@example.invalid>' rsa2048 sign 0
key_id="$(gpg --batch --with-colons --list-secret-keys | awk -F: '$1 == "sec" { print $5; exit }')"
mkdir -p packaging-stage repository-test-packages
gpg --batch --pinentry-mode loopback --passphrase "${REPO_GPG_PASSPHRASE}" \
    --armor --export-secret-keys > "${temporary_dir}/private.asc"
cp "${temporary_dir}/private.asc" packaging-stage/ci-test-key.asc
trap 'rm -f packaging-stage/ci-test-key.asc; rm -rf "${temporary_dir}"' EXIT

# Architecture-neutral fixture: only repository metadata is tested here.
printf '#!/bin/sh\nexit 0\n' > packaging-stage/ltbox
chmod +x packaging-stage/ltbox
sed 's|__LTBOX_EXEC__|/usr/bin/ltbox|g' \
    misc/desktop/io.github.miner7222.LTBox.desktop \
    > packaging-stage/io.github.miner7222.LTBox.desktop
for arch in amd64 arm64; do
    case "${arch}" in
        amd64) rpm_arch=x86_64 ;;
        arm64) rpm_arch=aarch64 ;;
    esac
    for format in deb rpm; do
        printf '%s\n' "${format}" > packaging-stage/ltbox.install-source
        if [[ "${format}" == deb ]]; then
            name="ltbox_1.2.3_${arch}.deb"
        else
            name="ltbox-1.2.3-1.${rpm_arch}.rpm"
        fi
        docker run --rm -v "${PWD}:/work" -w /work \
            -e NFPM_ARCH="${arch}" -e NFPM_VERSION=1.2.3 \
            -e NFPM_RPM_SIGNING_KEY_FILE=/work/packaging-stage/ci-test-key.asc \
            -e NFPM_RPM_SIGNING_KEY_ID="${key_id}" \
            -e NFPM_RPM_PASSPHRASE="${REPO_GPG_PASSPHRASE}" \
            ghcr.io/goreleaser/nfpm:v2.47.0 package \
            --config packaging/linux/nfpm.yaml --packager "${format}" \
            --target "/work/repository-test-packages/${name}"
        (cd repository-test-packages && sha256sum "${name}" > "${name}.sha256")
    done
done
bash packaging/linux/build_repository.sh --tag v1.2.3 \
    --packages-dir repository-test-packages --output-dir repository-test-site \
    --private-key "${temporary_dir}/private.asc"
bash packaging/linux/validate_repository.sh repository-test-site
