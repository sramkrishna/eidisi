project('eidisi',
  version: '0.1.0',
  meson_version: '>= 0.37.0'
)

i18n = import('i18n')
python3 = import('python3')
prefix = get_option('prefix')
pkgdatadir = join_paths(prefix, get_option('datadir'), meson.project_name())
pythondir = python3.sysconfig_path('purelib')
install_subdir('eidisi', install_dir: pythondir)
subdir('data')
subdir('bin')
subdir('po')
meson.add_install_script('scripts/meson_post_install.py')

if get_option('with-flatpak')
  # We keep a generic manifest in the repo you can use but
  # we want builds to use the local files so simply rewrite it
  make_local_manifest = find_program('scripts/make_local_manifest.py')
  local_manifest = custom_target('manifest',
    input: 'dist/flatpak/me.ramkrishna.Eidisi.json',
    output: 'me.ramkrishna.eidisi.json',
    command: [make_local_manifest, '@INPUT@', '@OUTPUT@']
  )

  # Build a bundle for both testing and releases
  build_flatpak = find_program('scripts/build_flatpak.py')
  custom_target('flatpak',
    input: local_manifest,
    output: 'me.ramkrishna.Eidisi.flatpak',
    command: [build_flatpak, '@INPUT@', '@OUTPUT@'],
    build_always: true
    # TODO: This shouldn't build unless explicit
  )
endif
