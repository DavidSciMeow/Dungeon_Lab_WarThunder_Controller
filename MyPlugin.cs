using DGLablib;
using DGLablib.PluginContracts;
using System;
using System.Collections.Generic;
using System.ComponentModel.Composition;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Windows.Media.Capture;

namespace WarthunderDLL
{
    [Export(typeof(IPlugin))]
    public class MyPlugin : IPlugin
    {
        public string Name => "战雷郊狼控制器";
        public string? Description => "";
        public Dictionary<string, string> Settings { get; } = new() {
            { "波形频率(ms)", "60" },
            { "G力乘数", "10" },
            { "默认电压大小", "10" },
            { "成员组增益上限", "20" },
            { "成员组死亡增加", "100" },
        };


        public void Init(CoyoteDeviceV3 dev, CancellationToken ctl)
        {
            var init_ = byte.Parse(Settings["默认电压大小"]);
            byte intensity = init_;
            int is_died = 0;

            dev.Start();

            while (true)
            {
                if (ctl.IsCancellationRequested) return;

                WarthunderTelemetry.Data.Army.GetInfoAsync().GetAwaiter().GetResult();

                var type = WarthunderTelemetry.Data.Army.Type;
                var cr = WarthunderTelemetry.Data.Army.IndicatorsInfo?.Crew_current ?? 1;
                var call = WarthunderTelemetry.Data.Army.IndicatorsInfo?.Crew_total ?? 1;
                var g = WarthunderTelemetry.Data.Army.StateInfo?.Ny ?? 0;
                var isdrisurv = WarthunderTelemetry.Data.Army.IndicatorsInfo?.Driver_state == 1;
                var isgunsurv = WarthunderTelemetry.Data.Army.IndicatorsInfo?.Gunner_state == 1;

                if (type == 0)
                {
                    intensity = (byte)(init_ + (Math.Abs(g - 1) * byte.Parse(Settings["G力乘数"])));
                }
                else if(type == 1)
                {
                    if(call != 0)
                    {
                        intensity = (byte)(init_ + (1 - cr / (double)call) * byte.Parse(Settings["成员组增益上限"]));
                        if (isdrisurv && isgunsurv)
                        {
                            is_died++;
                            if (is_died < 10)
                            {
                                intensity += byte.Parse(Settings["成员组死亡增加"]);
                            }
                            else
                            {
                                is_died = 10;
                                intensity = init_;
                            }
                            Debug.WriteLine(is_died);
                        }
                    }
                }

                {
                    var frequency = int.Parse(Settings["波形频率(ms)"]);
                    byte _frequency = frequency > 255 ? (byte)255 : (byte)frequency;
                    byte _intensity = intensity > 255 ? (byte)255 : intensity;
                    var k = new WaveformV3(_intensity, [_frequency, _frequency, _frequency, _frequency]);
                    dev.WaveNow = k;
                }

                try
                {
                    Task.Delay(500, ctl).Wait(ctl);
                }
                catch
                {

                }
            }
        }

        public void Stop(CoyoteDeviceV3 dev, CancellationToken ctl) => dev.Stop();
    }
}
