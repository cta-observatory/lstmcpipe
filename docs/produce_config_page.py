from pathlib import Path
import markdown
import yaml
import git



def convert_markdown(text):
    """Convert Markdown text to HTML."""
    return markdown.markdown(text, extensions=["extra"])


def build_html_table_with_card(rows, headers=None):
    """Build an HTML table with a special card formatting in the 'readme' cell."""

    # Inline CSS for table and card styling.
    style = """
    <style>
      table {
          border-collapse: collapse;
          width: 100%;
          margin-bottom: 20px;
          text-align: left;
      }
      th, td {
          border: 1px solid #ddd;
          padding: 8px;
          vertical-align: top;
      }
      th {
          background-color: #f2f2f2;
          text-align: left;
      }
      /* Card styling for the readme cell */
      .readme-card {
          border: 1px solid #ccc;
          border-radius: 8px;
          padding: 15px;
          background-color: #fff;
          box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
      }
      a {
          color: #1a73e8;
          text-decoration: none;
      }
      a:hover {
          text-decoration: underline;
      }
    /* Reduce the size of h1 titles */
      h1 {
          font-size: 24px;
      }
    </style>
    """

    table_html = [style, "<table>"]

    # Build the header row if headers are provided.
    if headers:
        table_html.append("  <thead>")
        table_html.append("    <tr>")
        for header in headers:
            table_html.append(f"      <th>{convert_markdown(str(header))}</th>")
        table_html.append("    </tr>")
        table_html.append("  </thead>")

    table_html.append("  <tbody>")
    for row in rows:
        commit_date, prod_markdown, readme_markdown = row
        table_html.append("    <tr>")
        table_html.append(f"      <td>{commit_date}</td>")
        table_html.append(f"      <td>{convert_markdown(prod_markdown)}</td>")
        # Readme cell with card styling
        readme_html = f'<div class="readme-card">{convert_markdown(readme_markdown)}</div>'
        table_html.append(f"      <td>{readme_html}</td>")
        table_html.append("    </tr>")
    table_html.append("  </tbody>")
    table_html.append("</table>")

    return "\n".join(table_html)


def load_config(filename):
    with open(filename, "r") as f:
        return yaml.safe_load(f)


def add_prod_table(
    production_dir,
    outfile,
    lstmcpipe_repo_prod_config_url="https://github.com/cta-observatory/lstmcpipe/tree/master/production_configs/",
    root_dir=None,
):
    """
    Generate an HTML table summarizing production configurations and save it to a file.

    production_dir : pathlib.Path or str
        Path to the production configs directory.
    outfile : str
        Path to the output file where the HTML table will be saved.
    lstmcpipe_repo_prod_config_url : str, optional
        Base URL for the production configs in the lstmcpipe repository (default is 
        "https://github.com/cta-observatory/lstmcpipe/tree/master/production_configs/").
    root_dir : str, optional
        Root directory for the git repository (default is None).

    Returns
    -------
    None
    """

    commit_times = []
    prod_list = []
    for prod_dir in [d for d in Path(production_dir).iterdir() if d.is_dir()]:
        commit = list(git.Repo(root_dir).iter_commits(paths=prod_dir))[-1]

        yml_list = [f for f in prod_dir.iterdir() if f.name.endswith(".yml") or f.name.endswith(".yaml")]

        if yml_list:
            try:
                conf = load_config(yml_list[0])
            except:  # noqa
                print(f"Could not load prod id for {prod_dir.name}")
        else:
            print(f"No yml file in {prod_dir}")

        markdowns = list(prod_dir.glob("*.md"))
        readme = open(markdowns[0]).read() if markdowns else ""

        prod_list.append(
            [
            commit.authored_datetime.date(),
            f"[{prod_dir.name}]({lstmcpipe_repo_prod_config_url + prod_dir.name})",
            readme,
            ]
        )
        commit_times.append(commit.authored_datetime)

    sorted_lists = sorted(zip(commit_times, prod_list))
    prod_list = [prod for _, prod in sorted_lists]

    prod_list.reverse()  # Reverse the ordering to have the most recent first

    headers = ["Production date", "Prod ID", "Readme"]

    # Generate the HTML table.
    html_table = build_html_table_with_card(prod_list, headers=headers)

    # Save the table to a file for inclusion in Sphinx documentation.
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html_table)


if __name__ == "__main__":
    root_dir = Path(__file__).parent.joinpath("..").resolve()
    prod_dir = root_dir.joinpath("production_configs")
    outfile = Path(__file__).parent.joinpath("productions_table.html")
    add_prod_table(prod_dir, root_dir=root_dir, outfile=outfile)
