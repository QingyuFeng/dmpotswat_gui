# 针对SWAT模型的分布式模型参数优化工具用户手册

针对SWAT模型的分布式模型参数优化工具是一个基于分布式最优化模式对SWAT模型进行多变量多站点校验的工具。

## 什么是分布式模型参数优化模式？

分布式模型参数优化模式，顾名思义，就是通过分布式的方式来进行参数的最优化。通常情况下，对分布式模型的参数优化有两类模式。

第一类模式可以被称为“同时优化模式”，即通过对全流域的参数进行同时优化，确定能够适用于全流域并获得满足一定校验条件的一套最优参数。再利用这一种模式进行参数最优化的时候，暗含着这样一个假设：所确定的一套最优化参数能够适用于全流域，也就是说流域不同部位的水文过程对环境条件的响应是一致的，忽略了空间异质性。因此对于水文过程响应随地理空间变异不大的流域来说，这一忽略对参数优化结果没有影响。然而，对于较大一点的复杂流域来讲，其地理环境条件的空间异质性是不能够被忽略的，也就是说，一套参数并不能很好的反映这种空间异质性的影响。因此这种优化只能被称为“部分优化”或者“集总式优化”，而不是“全局优化”。尽管模型的参数设置是分布式的，模型参数的优化过程却采用了集总式的优化模式。

第二类模式被称为“顺序模式”，即按照一定顺序，通常是上游到下游，对流域的不同位置的参数进行分别优化。在优化过程中，对流域下一部分的参数进行优化时保持流域上一部分的参数不变。这一类模式就针对流域不同部位采用了相对应的最优参数。然而这种模式存在的问题是，如果流域划分为过多部分，则需要进行多次校验，对于较大流域来讲，校验通常需要上千次的运行，时间上并不可行。

为了解决这两类模式存在的问题，本软件提供了分布式的模型参数优化模式。根据用户提供的流域出口，软件依据深度优先算法进行流域的自动分组，将子流域划分为若干子流域组。然后对各个子流域组进行单独的优化算法，实现分布式参数优化。

Distributed model parameter optimization conducts parameter optimization in a distributed way. There are generally two schemes for multisite
calibration. One is simultaneous scheme which determines one optimal solution of parameter sets producing satisfactory calibration results for the whole
watershed. The other scheme is sequential scheme which optimizes objective functions in a cascading way. The determined optimal solution by the simultaneous scheme assumes that the selected optimal set of parameter values fits the whole watersheds. By assuming only one optimal parameter sets, spatial variation of hydrologic responses to geographical conditions in the calibration procedure is not fully captured. Thus, the simultaneous scheme might be suitable for calibrating models of watersheds with less geographic heterogeneity. For watersheds with large area or higher geographical heterogeneity, the optimal solution for the whole watershed cannot fit all areas. The solution is only "partially optimal" for
parts of the watershed instead of "global optimal" for the whole watershed. The scheme generating only one optimal solution for the whole watershed can be considered as "lumped optimization", even though the parameter values are setup in a distributed way. In order to fully capture the spatial variations of hydrologic processes, the modification of parameter values for multiple gauging stations need not to be identical but should be based on conditions of sub-watersheds as in the sequential scheme. The distributed model parameter optimization mode initialize parameters for each subarea group defined by users, and optimize them individually.

## 软件使用流程

本软件无需安装，双击Exe文件即可运行。

1. 打开软件：软件打开之后如下图所示

![1660545983190](image/Dmpotswat_Manual_Chinese/1660545983190.png)

这里一共有10个标签，分别对应10个相应的功能。

* Projects：项目设置标签，用于进行新项目构建、设置，以及已有项目的加载。
* SWAT Model：用于进行SWAT模型模拟相关的细节设置，包括模拟的起止日期、热身期、流域出口、各流域出口的校验变量、目标函数、权重等。
* Evaluate Default Model：用于进行模型默认参数情况下的目标函数状况。
* Parameter Selection：用于选择需要校验的参数。
* Sensitivity analysis：用于进行敏感性分析。
* Calibration：用于进行校验。
* Calibration Plotting：用于进行校验后各个运行次数的制图，主要绘制时间序列图和历时曲线图，用于辅助用于进行最优运行次数的选择。
* Select Best Run：用于依据各个运行次数的目标函数值，挑选所有子流域组目标函数都较小的运行次数，选择之后，程序将其应用到模型输入数据中，并计算响应的目标函数值，以及绘制响应的图。
* Uncertainty：绘制不确定性分析图。
* About：对软件基本情况的介绍。

2. Projects标签：

用户通过点击Create New Project按钮来新建一个项目。新建项目只需要选择一个文件夹，软件将在文件夹中创建项目文件（以dmp为后缀，如dmpotswat_demo.dmp）

![1660547589741](image/Dmpotswat_Manual_Chinese/1660547589741.png)

和如下的几个文件夹：

![1660547663647](image/Dmpotswat_Manual_Chinese/1660547663647.png)

* observeddata：用于存放保存有各个流域出口观测值文件的文件夹
* outfiles_dds：用于存放校验过程中计算的目标函数、所使用参数、参数选择等相关数据文件的文件夹
* outfiles_sa：用于存放敏感性分析过程中相应数据文件的文件夹
* reachshapefile：用于存放ArcSWAT生成的reach.shp文件的文件夹
* txtinout：用于存放原始SWAT模型输入输出文件的文件夹
* workingdir：用于存放运行过程中SWAT模型输入输出文件的文件夹

项目构建好之后，界面如下：

![1660551270652](image/Dmpotswat_Manual_Chinese/1660551270652.png)

项目构建之后，需要将SWAT的输入文件（txtinout）中的内容和reach.shp文件拷贝到上述相应文件夹中。然后在相应复选框中打勾。打勾后，程序会寻找该文件夹中的相应内容，如果没有拷贝，则无法打上，导致无法保存。如果都已经拷贝完成，下面文本框中将显示确认信息，可点击Save Project按钮来保存项目。此时，SWAT Model标签被打开，开始设置SWAT模拟相关参数。

如果之前有构建好的项目，可以点击Open Existing Project按钮来打开项目。点击之后，软件会首先检查是否现有项目正在运行，如果有，则提示是否保存当前项目，确认之后可以打开之前的项目。

3. SWAT Model标签

该标签在保存项目之后才会被激活。

进入标签进行相应的设置，需要设置的参数包括模拟开始和结束日期（要求格式为mm/dd/yyyy）、模拟热身期（Warmup Period)、输出时间频率（Time Frequency）和总共的流域出口和输出变量组合数量。其中流域出口和输出变量组合数量设定，是指按照输出变量来计算的，比如一个流域出口同时校验径流和泥沙量，那么该数量就需要被设置为2。该程序最多允许15个流域出口和输出变量组合，超过该数字将报错。

设置好之后点击Define Detail按钮进行详细设置，需要设置的参数包括流域在reach.shp文件中对应的出口数字、各流域出口需要校验的变量数字（变量对应的数字名称在窗口最下面显示）、每个组合的权重、所需要的统计变量、以及统计变量的权重。这里有两个层次的权重，第一层次是流域出口和输出变量组合的权重，比如有三个组合，如果用户对某一个组合比较重视，可以设置较大的数字。第二层次是同一个组合下不同统计值的权重，用户可以选择一个或多个统计值，如果用户对该组合某一个统计值（比如纳什系数）比较重视，可以设置较大权重。权重在计算过程中将依据所有组合或统计值的权重进行归一化处理，这一设置是方便用户不用纠结具体的数字，而是提供相对大小，便可进行权重设置。

设置好之后，点击Save Details按钮进行保存。如果保存成功

保存好之后，用户需要将存有对应观测值数据的文件拷贝到上述对应文件夹中，然后在复选框中打勾，软件会对每一个流域出口的相应观测值文件进行检测，如果没有，则会报错。如果成功，将显示存在的确认信息，点击OK关闭弹出窗口。

![1660551519647](image/Dmpotswat_Manual_Chinese/1660551519647.png)

待SWAT模型校验参数设置成功之后，其他标签将被激活。

4. Evaluate Default Model标签

该标签的功能是计算模型在默认输入参数下的统计值和目标函数值，为用户提供一个参考，了解模型初始的状态。直接点击Run Default Model按钮开始运行。运行过程中，程序首先将txtinout文件夹内的输入文件拷贝到workingdir文件夹下，然后运行SWAT模型，运行完毕之后，读取相应的观测值和模拟值，计算统计值和用户在SWAT Model标签内定义的统计值和目标函数值。最终结果并没有输出到文件，仅在界面显示。

![1660569719508](image/Dmpotswat_Manual_Chinese/1660569719508.png)

5. Parameter selection标签

该标签用于辅助用户选择所需要校验的参数。该列表包含了66个在校验径流Flow（30个），泥沙量Sediment（10个），氮流失Nitrogen（17个）和磷流失Phosphorus（8个）时常用的参数。用户可以依据经验、文献推荐、或者进行下一步的敏感性分析之后来挑选合适的参数。选择好之后，点击Save Parm Selection按钮保存所选的参数。

![1660569946718](image/Dmpotswat_Manual_Chinese/1660569946718.png)

6. Sensitivity Analysis标签

注：Sobol方法正在进行测试，不一定能够给出有效结果，推荐使用Morris或者FAST方法。

该标签为用户提供了三种用于进行敏感性分析的方法，包括Sobol、Morris、FAST，均采用python敏感性分析扩展包SALib，详细的理论请参见[SALib - Sensitivity Analysis Library in Python — SALib 1.4.6b1.post1.dev2+g00d8e47.d20220712 documentation](https://salib.readthedocs.io/en/latest/index.html)。
进入标签后，用户可以通过点击多选框来选择希望使用的敏感性分析算法，输入对应的参数，点击Save SA Setting按钮保存之后，便可激活Run SA按钮，点击可以开始敏感性分析。

程序开始之后，将首先把TxtInout文件夹中的输入文件重新拷贝到workingdir文件夹中，然后进行参数抽样，抽样之后，利用所抽取的参数样本集合依次进行模拟，获得模拟结果之后，最终计算敏感性指标并存储到outfiles_sa文件夹中。

![1660570973335](image/Dmpotswat_Manual_Chinese/1660570973335.png)

7. Calibration标签

该标签的功能是基于动态维度优化算法（Dynamic Dimension Search，DDS）对模型的输入参数进行优化。

该标签主要需要首先对参数优化算法进行几项设置，包括：

* calibration mode：校验模式设置。这里提供了两个模式，一个模式成为“分布式”（Distributed），另外一个成为“集总式”（Lumped）。软件将首先依据用户提供的流域出口编号，通过深度优先搜索算法寻找各个流域出口上游的所有子流域。之后，利用分布式校验模式，对每一个流域出口对应的子流域集进行单独的优化过程；而利用集总式模式，则对整个流域采用同一套参数进行优化。参数优化之后，计算各个流域出口的统计值。
* initial parameter values：初始参数值。这里提供两个选项，随机选项（Random）和默认值选项（Initial）。随机选项是指在最初的几次运行时，采用随机函数，在各参数上下限范围内进行抽样，确定本次运行的参数值。而默认值选项，则采用Parameter Selection标签中所设置的默认值进行第一次计算。无论是随机起点还是默认值起点，初始参数值的设定都是为参数的优化过程提供一个起点。在用户规定的总运行次数（Total iterations），每一次运行，包含的步骤包括依据上一次的目标函数值进行参数抽样，将参数的抽样值写入模型输入数据，运行模型，获取模拟值，计算统计值和目标函数，依据目标函数值进行下一次运行，直到运行结束。而随机选项的优势是提供了一个较大的搜索空间，为寻找较好的参数提供较大的概率。
* pertubation factor：抽样间隔步频，用于DDS算法中参数值的确定，一般选取0.2默认值。
* total iterations：总运行次数。DDS优化算法的模拟机制在于从总的运行次数中，在特定次数（比如总数100次，运行到25次）时，依据次数来确定每一个参数被抽取到的比例，计算公式为probability = 1 - log(25)/log(100) = 0.301。然后再依据随机算法进行具体概率计算每一个参数被抽取到的概率。该方法的逻辑为随着运行次数的增加，被抽到的参数数量逐渐减少，以减少总的运行次数需求。如下图所示。
  ![1660616580335](image/Dmpotswat_Manual_Chinese/1660616580335.png)

  下图中纵轴是挑选的流域尺度的参数，对应每一行的黑色条带代表在某次运行中被抽到，而白色部分代表没有被抽到。可以看出，随着运行次数的增加，被抽到的参数数量在减少。而上图则是随着运行次数被抽到

  ![1660616261948](image/Dmpotswat_Manual_Chinese/1660616261948.png)
* restart mode：重启机制。如果因为某种原因程序中断，用户可以选择continue，程序将自动寻找上次终端的运行次数，并读取最后一次的参数值，以此为基点进行参数优化。

![1660574786733](image/Dmpotswat_Manual_Chinese/1660574786733.png)

8. Calibration Plotting标签

该标签为用户选择最优的参数提供辅助制图。通过点击Define Plot Details按钮，程序将自动加载在SWAT Model标签中定义的流域出口和变量组合，用户需要选择制作时间序列线图和历时曲线图，可同时选择。并填入在1和Calibration标签中总运行次数（Total Iteration）之间的任意数字，然后点击Save Plot Details保存。

![1660727780079](image/Dmpotswat_Manual_Chinese/1660727780079.png)

保存之后激活Create Plots按钮，程序将开始进行绘图，绘图结果如下图。

![1660727884600](image/Dmpotswat_Manual_Chinese/1660727884600.png)

![1660727866667](image/Dmpotswat_Manual_Chinese/1660727866667.png)

9. Select Best Run标签

该标签用于辅助用户挑选在校验过程中提供最好校验结果的次数，挑选之后，程序将自动将该次运行的参数应用到模型中，获得校验好的模型。结合SWAT Model标签中的起始和截至模拟时间的功能，可以进行校正（Calibration）和验证（Validation）期模型模拟、统计值和目标函数计算，以及进行制图。这个标签可以同上一个标签配合使用，依据目标函数值来挑选需要制图的运行次数，然后用Plotting功能来进行绘制，辅助选择最优的参数。选定之后，点击Save Best Parameter Set来保存选择的次数，之后激活Run With Best Parameter Set来进行运行，也可以在这里调用绘图，绘制结果同上。

![1660728524883](image/Dmpotswat_Manual_Chinese/1660728524883.png)

10. Uncertainty标签

目前版本中，该标签主要的功能是绘制不确定性图，用户可以输入在图中需要的最优结果运行次数，点击Run Uncertainty进行绘制。

![1660728716936](image/Dmpotswat_Manual_Chinese/1660728716936.png)

绘制结果如下

![1660728748906](image/Dmpotswat_Manual_Chinese/1660728748906.png)
