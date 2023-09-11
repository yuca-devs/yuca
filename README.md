# yuca

Keep all your info (contact, education, projects, publications, etc) in a single
place and generate Resumes, CVs, and much more in one line.

## Installation

```bash
pip install yuca
```

## Getting started

You can enter your data from partially filled data files generated using:

```bash
yuca warehouse init my_wh_name
```

That will create your **warehouse**, which is the folder where you are going to
store your **data**, **templates** and **recipes**.

By default, no templates are downloaded with yuca. In order to get your first
template, you can run:

```bash
yuca template get https://github.com/yuca-devs/forty-seconds-resume.git
```

That will add the template *forty-seconds-resume* into the *templates* folder
of your warehouse. Moreover, it will create a *forty-seconds-resume-base-recipe*
that helps yuca while cooking that template. You can find the base recipe in the
**recipes** folder of your warehouse.

Now, you can produce a compiled version of your template by cooking the recipe:

```bash
yuca cook forty-seconds-resume-base-recipe
```

That will produce a folder *forty-seconds-resume-base-recipe-cooked* with the
result of the compilation.

Finally, you can edit the file *en.yml* inside the **data** folder of your
warehouse, insterting your own personal information. Then cook the recipe again
to see the template filled up with your data.
