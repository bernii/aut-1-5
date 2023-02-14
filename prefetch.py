from modules import shared, devices, sd_samplers, upscaler, extensions, localization, ui_tempdir, ui_extra_networks
import modules.codeformer_model as codeformer
import modules.face_restoration
import modules.gfpgan_model as gfpgan
import modules.img2img

import modules.lowvram
import modules.paths
import modules.scripts
import modules.sd_hijack
import modules.sd_models

from modules import modelloader

print("pre-downloading things required by model")


modelloader.cleanup_models()
modules.sd_models.setup_model()

modelloader.list_builtin_upscalers()
modules.scripts.load_scripts()
modelloader.load_upscalers()

modules.textual_inversion.textual_inversion.list_textual_inversion_templates()
modules.sd_models.load_model()
